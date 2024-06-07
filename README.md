<h1 align="center"> VenomShield 🛡️ Discord Bot </h1>

Welcome to VenomShield, your NFT guardian on Discord! This bot helps you verify holders on the Venom Network and manage roles based on users' NFT holdings.

## 🛠️Instructions to Set Up the Bot:

1. **Clone the Repository**: 

```sh
https://github.com/BrahimChatri/venom-holders-verify.git
```

2. **Create Environment Variables**:

Rename `.env.dev`To `.env` and Remplace values of  following variables :

```sh
TOKEN = Your Discord bot token 
ALLOWED_USER_ID = Your Discord ID 
```

3. **Install Dependencies**:

```sh
pip install -r requirements.txt
```


4. **Run the Bot**:

```sh 
python main.py 
```



5. **Authorize the Bot on Your Server**:
Invite the bot to your Discord server using the generated OAuth2 URL and grant necessary permissions.

## ✨ Bot Features:

- **Wallet Verification**: Users can submit their wallet addresses to verify their NFT holdings.
- **Automatic Role Assignment**: Based on the submitted NFT data, users will be assigned roles automatically.
- **Background Task**: Periodically verifies NFTs to ensure role assignments are up to date.
- **Administrative Commands**: Administrators can set up verification channels and access bot logs.

## 📖 How to Use:

1. **Fill Authorization Form**: Fill out the authorization form to get access to the bot's features.
2. **Set Verification Channel**: Administrators can set the verification channel using the `/set_embed_channel` command.
3. **Submit Wallet**: Users can submit their wallet addresses through the provided interface.
4. **Get Verified**: After verification, users will gain access to exclusive channels and content based on their NFT holdings.
- __You can customize embed info by default set to be server icon as thumbnail and image are set to verify gif visit [assets](./assets/) To see some pics of the bot__ 

## 🌟 Contribution and Feedback:

Feel free to use this bot as you like! If you find it useful or have suggestions for improvement, don't __hesitate to star the repository and follow Me on GitHub__.


[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https://github.com/BrahimChatri/venom-holders-verify&title=Views)](https://hits.seeyoufarm.com)

## 📜 License:

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


