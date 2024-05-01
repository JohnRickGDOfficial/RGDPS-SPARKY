const Eris = require("eris");
const keep_alive = require('./keep_alive.js')

// Replace TOKEN with your bot account's token
const bot = new Eris(process.env.token);

bot.on("error", (err) => {
  console.error(err); // or your preferred logger
});

bot.on("messageCreate", (msg) => {
  // Check if the message starts with the prefix and is not from a bot
  if (msg.content.startsWith("!ping") && !msg.author.bot) {
    // Send a reply with the latency between the bot and the Discord API
    const latency = bot.shards.reduce((prev, shard) => prev + shard.latency, 0) / bot.shards.size;
    msg.channel.createMessage(`Pong! Latency is ${latency.toFixed(2)}ms.`);
  }
});

bot.connect(); // Get the bot to connect to Discord
