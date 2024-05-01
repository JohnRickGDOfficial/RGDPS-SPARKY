const Eris = require("eris");
const keep_alive = require('./keep_alive.js')

// Replace TOKEN with your bot account's token
const bot = new Eris(process.env.token);

// Map to store points for users
const userPoints = new Map();

bot.on("error", (err) => {
  console.error(err); // or your preferred logger
});

bot.on("messageCreate", async (msg) => {
  // Check if the message is not from a bot
  if (!msg.author.bot) {
    // Check if the message starts with the guess command
    if (msg.content.startsWith("!guess")) {
      // Randomly select a picture name, replace this with your logic
      const pictureName = "example";

      // Send a message indicating the picture to guess
      await msg.channel.createMessage(`Guess the name of the picture: ${pictureName}`);

      // Wait for 10 seconds for the user's guess
      const filter = (m) => m.author.id === msg.author.id;
      try {
        const collected = await msg.channel.awaitMessages(filter, { max: 1, time: 10000, errors: ['time'] });
        const guess = collected.first().content.toLowerCase();

        // Check if the user's guess is correct
        if (guess === pictureName.toLowerCase()) {
          // Reward the user with 10 points
          userPoints.set(msg.author.id, (userPoints.get(msg.author.id) || 0) + 10);
          await msg.channel.createMessage(`Congratulations, ${msg.author.username}! You guessed it right. You earned 10 points.`);
        } else {
          await msg.channel.createMessage(`Sorry, ${msg.author.username}. Your guess was incorrect.`);
        }
      } catch (err) {
        await msg.channel.createMessage(`Time's up, ${msg.author.username}.`);
      }
    } else if (msg.content.startsWith("!points")) {
      // Command to check user's points
      const points = userPoints.get(msg.author.id) || 0;
      await msg.channel.createMessage(`You have ${points} points.`);
    }
  }
});

bot.connect(); // Get the bot to connect to Discord
