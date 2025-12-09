// services/aliossService.js
const OSS = require("ali-oss");
class AliOSSService {
    constructor() {
        this.client = null;
        this.init();
    }
    init() {
        this.client = new OSS({
            region: process.env.OSS_REGION,
            accessKeyId: process.env.OSS_ACCESS_KEY_ID,
            accessKeySecret: process.env.OSS_ACCESS_KEY_SECRET,
            bucket: process.env.OSS_BUCKET,
            secure: true,
        });
    }

    async getImageUrl(imageName) {
        try {
            console.log("Checking existence of image:", imageName);
            await this.client.head(imageName);
            return this.client.signatureUrl(imageName, {
                expires: 3600,
                response: {
                    "content-disposition": "inline",
                },
            });
        } catch (error) {
            if (error.code === "NoSuchKey") {
                throw new Error("Image Not Found");
            }
            throw error;
        }
    }
}
module.exports = AliOSSService;
