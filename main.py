import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from dotenv import load_dotenv 
import requests
import logging
import aiofiles
import json
import os
import io

load_dotenv()

TOKEN = os.getenv("TOKEN")
DATA_FILE = 'user_data.json' # file to store user data
LOGS_FILE = 'bot.log' # file to stor logs 
ALLOWED_USER_ID =int(os.getenv("ALLOWED_USER_ID")) # get id and convert it to int 
AUTHORIZED_GUILD_IDS = [
    1111111111111111111,
    1243214590124001100
    ] # remplace with authorized guilds ids 

# Configuration for server-specific collections
collection_config = {
    "Venom Cats": {  # name of the collection 
        "server_id": 1111111111111111, 
        "contract_address": "0:7cb8xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  
        "roles": {
           "1+": 0000000000000000000,
           "5+" : 1111111222222222222,
           "10+": 1125402001222222222,
           "30+": 2121212121212121212,
        }
    } # This is an Example of how to store data for ur server !! Note that name of roles should stay like this "number of holding nfs +" remplace id  
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,  #logging level
    format='%(asctime)s [%(levelname)s] %(message)s',  #format of the log messages
    handlers=[
        logging.FileHandler('bot.log'),  # Log to a file to be able to see logs from server by using /logs
    ]
)

logger = logging.getLogger(__name__)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='*', intents=intents)

# Modal for submitting wallet address
class WalletModal(discord.ui.Modal, title='Submit Your Wallet Address'):
    wallet_address = discord.ui.TextInput(label='Wallet Address', placeholder='Eg:0:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

    async def on_submit(self, interaction: discord.Interaction):
        """
        Handles the submission of a wallet address by a user.

        Args:
            interaction (discord.Interaction): The interaction object containing user and guild information.
        """
        user_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)
        
        # Load user data
        user_data = load_user_data()
        
        user_wallet = self.wallet_address.value.strip()
        logger.info(f'User {interaction.user} submitted wallet address {user_wallet}')

        # Check if the wallet address is already submitted
        for other_user_id, servers in user_data.items():
            if other_user_id != user_id:  # Ignore the same user
                if any(user_wallet == info.get('wallet_address') for info in servers.values()):
                    await interaction.response.send_message("This wallet address has already been submitted by another user. Please submit your own wallet.", ephemeral=True)
                    return

        # Initialize user's data if not present
        if user_id not in user_data:
            user_data[user_id] = {}

        collection_contract_addresses = [config["contract_address"] for config in collection_config.values()]
        nft_data = get_user_data(user_wallet, collection_contract_addresses)

        if nft_data:
            messages = [f"User: {interaction.user.mention} has:"]
            for collection, count in nft_data.items():
                messages.append(f"{count} NFTs in {collection}")

            await interaction.response.send_message("\n".join(messages), ephemeral=True)
            logger.info(f'User {interaction.user} holds: {nft_data}')
            guild = interaction.guild
            member = guild.get_member(interaction.user.id)
            if member:
                await process_nft_data(guild, member, nft_data)

            user_data[user_id][server_id] = {'wallet_address': user_wallet}
            save_user_data(user_data) # Save user data to a file to access it in the task loop 
        else:
            await interaction.response.send_message("Failed to retrieve user data. Try again later!", ephemeral=True)

class PersistentWalletView(discord.ui.View):
    def __init__(self):
        """
        Initializes the class instance, setting up a Discord UI button with a callback.

        The button is labeled "Submit Wallet" and styled as a success button.
        The button's callback is set to the `button_callback` method.
        """
        super().__init__(timeout=None)
        button = discord.ui.Button(label="Submit Wallet", style=discord.ButtonStyle.success, custom_id="submit_wallet_button")
        button.callback = self.button_callback
        self.add_item(button)
    async def button_callback(self, interaction: discord.Interaction):
        """
        Handles the button interaction callback.

        This method checks if the interaction is from an authorized guild. If not, it sends an
        authorization error message with instructions on how to get the server authorized. If the
        guild is authorized, it sends a modal for further interaction.

        Args:
            interaction (discord.Interaction): The interaction object representing the button click.
        """
        if interaction.guild_id not in AUTHORIZED_GUILD_IDS:
            # If the server ID is not in the authorized list, send an authorization error message
            embed = discord.Embed(
                title="Authorization Error ❌",
                description="It seems like your server hasn't been added to the bot yet.",
                color=discord.Color.dark_red()
            )
            embed.add_field(
                name="Action Required",
                value="To add your server and access the bot's features, please fill out this form:\nOwner will immediately add ur serve enjoy ur day ",
                inline=False
            )
            embed.add_field(
                name="Server Authorization Form",
                value="[Authorization Form](https://example.com)",
                inline=False
            )
            embed.set_footer(
                text="Thank you for your cooperation!"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Send the modal to be filled if the server is in the authorized list
        await interaction.response.send_modal(WalletModal())

# Function to fetch user's NFT data using venomart marcketplace api 
def get_user_data(user_wallet, collection_contract_addresses):
    """
    Fetches NFT data for a given user wallet and filters it based on specified collection contract addresses.

    Args:
        user_wallet (str): The wallet address of the user.
        collection_contract_addresses (list): A list of NFT collection contract addresses to filter the data.

    Returns:
        dict: A dictionary where keys are collection names and values are the count of NFTs in those collections.
              Returns None if the API request fails.

    Raises:
        None
    """
    API_URL = f"https://venomart.io/api/nft/get_owner_nfts?filterCollection=&owner_address={user_wallet}&saleType=All&sortby=recentlyListed&minprice=0&maxprice=0&skip=0"
    response = requests.get(API_URL)
    
    # Check if the response is 200 
    if response.status_code == 200:
        data = response.json()
        nft_data = {}

        for nft in data["data"]:
            contract_address = nft["NFTCollection"]["contractAddress"]
            collection_name = nft["NFTCollection"]["name"] 

            if contract_address in collection_contract_addresses:
                if collection_name not in nft_data:
                    nft_data[collection_name] = 0
                nft_data[collection_name] += 1

        return nft_data
    else:
        logger.error(f'Failed to fetch data for wallet {user_wallet}, status code: {response.status_code}')
        print("Error:", response.status_code)
        return None

# Save user data
def save_user_data(user_data):
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f)

# Load user data
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Background task to verify NFTs periodically
@tasks.loop(minutes=30)
async def verify_nfts():
    """
    Verifies NFTs for users across different servers.

    This function loads user data, iterates through each user and their associated servers,
    retrieves NFT data for the user's wallet, and processes the NFT data if available.

    Steps:
    1. Load user data.
    2. Iterate through each user and their servers.
    3. Retrieve NFT data for the user's wallet.
    4. If NFT data is found, get the guild and member information.
    5. Process the NFT data for the member in the guild.

    Returns:
        None
    """
    user_data = load_user_data()
    for user_id, user_info in user_data.items():
        for server_id, server_info in user_info.items():
            user_wallet = server_info['wallet_address']
            collection_contract_addresses = [config["contract_address"] for config in collection_config.values()]
            nft_data = get_user_data(user_wallet, collection_contract_addresses)
            if nft_data:
                guild = bot.get_guild(int(server_id))
                if guild:
                    member = guild.get_member(int(user_id))
                    if member:
                        await process_nft_data(guild, member, nft_data)

async def process_nft_data(guild, member, nft_data):
    """
    Processes NFT data for a given guild and member, assigning or removing roles based on the NFT collection count.

    Args:
        guild (discord.Guild): The guild (server) where the roles are managed.
        member (discord.Member): The member whose roles are to be updated.
        nft_data (dict): A dictionary containing NFT collection names as keys and their respective counts as values.

    Returns:
        None
    """
    for collection, count in nft_data.items():
        if collection in collection_config and collection_config[collection]["server_id"] == guild.id:
            roles = collection_config[collection]["roles"]
            for threshold, role_id in roles.items():
                role = guild.get_role(role_id)
                if role:
                    if threshold.endswith('+') and count >= int(threshold[:-1]):
                        await member.add_roles(role)
                    elif threshold.endswith('+') and count < int(threshold[:-1]):
                        await member.remove_roles(role)
                        await member.remove_roles(role)


# Event when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    synced = await bot.tree.sync() # sync the commands 
    print(f"Synced {len(synced)} commands")
    logger.info(f'Synced {len(synced)} commands')
    activity = discord.Activity(type=discord.ActivityType.watching, name="Users Wallets") 
    await bot.change_presence(activity=activity) # Update bot activity 
    verify_nfts.start() # Start Background task
    bot.add_view(PersistentWalletView()) #add the view

@bot.tree.command(name="help", description="Get some help!")
async def help(interaction: discord.Interaction):
    guild= interaction.guild
    icon_url = interaction.guild.icon.url if guild.icon else None
    embed = discord.Embed(
    title="Help",
    description="**Here is some help for bot utilization.**\n\n\n",
    color=discord.Color.brand_green()
    )
    embed.add_field(
        name="Getting Started",
        value="To start using the bot's features, make sure the bot has been properly set up and authorized in your server.",
        inline=False
    )
    embed.add_field(
        name="About Bot",
        value="""
    **VenomShield:** The NFT guardian you need. 
    This bot verifies holders on the Venom Network and manages roles based on users' NFT holdings.
    """,
        inline=False
    )
    embed.add_field(
        name="Bot Usage",
        value="""Here is how you can use the bot's features:\n
     1 . **Set the Verification Embed Channel**: Use the `/set_embed_channel` command (administrators only) to specify the channel where users can submit their wallets.
     2 . **Submit Wallet**: Users can submit their wallet addresses through the provided interface to get verified.
     3 . **Get Roles**: Once verified, users will be assigned roles based on their NFT holdings.
     4 . **Enjoy the Bot**: Access exclusive channels and content based on your roles.""",
        inline=False
    )
    embed.add_field(
        name="Future Updates",
        value="We plan to add more features such as a website for connecting wallets, viewing portfolios, and more, based on user support and feedback. Stay tuned! __[Github](https://github.com/BrahimChatri/venom-holders-verify)__",
        inline=False
    )
    embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text=f"© 2024 - {interaction.guild.name}", icon_url=icon_url)


    await interaction.response.send_message(embed=embed, ephemeral=False)

    

# Command to send embed to specified channel (for administrators)
@bot.tree.command(name="set_embed_channel", description="Send verify embed to the specified channel. (This command is only for administrators)")
async def set_embed_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild = interaction.guild
    member = guild.get_member(interaction.user.id)
    if member and member.guild_permissions.administrator:
        try : 
            await send_verification_embed(channel, interaction) # send embed 
            await interaction.response.send_message(f"Embed sent to {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in that channel.(give the bot permission)", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)


# Function to send verification embed
async def send_verification_embed(channel, interaction: discord.Interaction):
    """
    Sends a verification embed message to a specified Discord channel.

    This function constructs and sends an embed message to the provided channel,
    prompting users to verify their NFT holdings by submitting their wallet address.

    Args:
        channel (discord.TextChannel): The channel where the embed message will be sent.
        interaction (discord.Interaction): The interaction object containing context about the command invocation.

    Returns:
        None
    """
    current_date_utc = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    guild = interaction.guild
    guild_name = guild.name
    guild_icon_url = guild.icon.url if guild.icon else None

    embed = discord.Embed(
        title="**__Wallet Verification__**",
        description=(
            "**Welcome to the Venom verification bot!**\n\n"
            "To gain access to exclusive channels and content, please verify your NFT holdings by submitting your wallet address.\n\n"
            "Click the button below to start the verification process.\n"
        ),
        color=discord.Colour.dark_green()
    )
    embed.set_thumbnail(url=guild_icon_url)
    embed.set_image(url="https://cdn.discordapp.com/attachments/1133943811006025772/1242652573958275154/TwitterVerifiedIconGIF_2.gif?ex=664e9de5&is=664d4c65&hm=02caa7fe7597a83488f7dfcbb1f5039c5bc5cf381eecde7d5ce6134b5ee09cd8&")
    embed.add_field(name="Why Verify?", value="Verification allows you to access exclusive channels and content.", inline=False)
    embed.add_field(name="How to Verify?", value="Click the button below and enter your wallet address.", inline=False)
    embed.add_field(name="Requirements : ", value="Ensure your wallet contains the required NFTs.\n Othewise you will get `Failed to retrieve user data. Try again later!`", inline=False)
    embed.set_footer(text=f"© 2024 {guild_name} - {current_date_utc} ", icon_url=guild_icon_url)

    await channel.send(embed=embed, view=PersistentWalletView())
# This command to access the data from server from allowed user !!
@bot.tree.command(name="dev_things", description="This command is restricted to the Owner !!")  
async def show_data(interaction: discord.Interaction):
    guild = interaction.guild
    member = guild.get_member(interaction.user.id)
    if member and member.id == ALLOWED_USER_ID :
        try:
            with open(DATA_FILE, 'r') as file:
                await interaction.response.send_message("**__Here is your data:__**", file=discord.File(file, "user_data.json"))
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True) 
    else:
        await interaction.response.send_message("You don't have permission to use this command. Only Owner can use it ", ephemeral=True)

@bot.tree.command(name="logs", description="This command is restricted to the Owner !!") #this command to access bot logs from server
async def stats(interaction: discord.Interaction):
    guild = interaction.guild
    member = guild.get_member(interaction.user.id)
    if member and member.id == ALLOWED_USER_ID: # check if member is the allowed one 
    
        try:
            # Use aiofiles to read the file asynchronously
            async with aiofiles.open(LOGS_FILE, 'rb') as file:
                file_data = await file.read()
                # Create a discord file object
                discord_file = discord.File(io.BytesIO(file_data), "bot.log")
                await interaction.response.send_message("**__Here is your logs file:__**", file=discord_file)
                logger.info(f'Owner accessed logs')
        except Exception as e:
            logger.error(f'An error occurred: {e}')
            try:
                await interaction.response.send_message(f"An error occurred: {str(e)}")
            except discord.errors.NotFound:
                logger.error("Failed to send error message: Interaction not found")
    else:
        try:
            await interaction.response.send_message("You don't have permission to use this command. Only Owner can use it", ephemeral=True)
        except discord.errors.NotFound:
            logger.error("Failed to send permission error message: Interaction not found")

@bot.command(name='servers') # this is a prefix command if you want to use it type '*servers' to see all the severs bot in  
async def list_servers(ctx):
    """List the servers the bot is currently in."""
    servers = bot.guilds
    server_list = "\n".join(f"**{server.name}** (ID: {server.id})" for server in servers)
    embed = discord.Embed(
        title="Servers",
        description=f"\n**Servers the bot is currently in:**\n\n{server_list}",
        color=discord.Color.dark_gold()
    )
    await ctx.send(embed=embed)


bot.run(TOKEN) # Run the bot 