import discord
from discord.ext import commands
import random
import os
from datetime import datetime, timedelta

# IDs (βάλε τα δικά σου)
SPIN_CHANNEL_ID = 1467585068934500618        # Κανάλι όπου επιτρέπεται το spin
LOG_CHANNEL_ID = 1467584551261049097         # Κανάλι logs
PANEL_CHANNEL_ID = 1467585068934500618       # Κανάλι όπου θα σταλεί το panel

# Cooldown 3.5 ώρες
COOLDOWN_HOURS = 3.5
user_cooldowns = {}

# Rewards με πιθανότητες
rewards = [
    ("try again later", 65),          # 60%
    ("VIP role", 25),                 # 15%
    ("custom logo", 5),   # 10%
    ("custom background", 5),           # 10%

]

bot = commands.Bot(command_prefix="!", intents=intents)


def pick_reward():
    items = [r[0] for r in rewards]
    weights = [r[1] for r in rewards]
    return random.choices(items, weights=weights, k=1)[0]


from discord.ui import View, Button

class SpinButton(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(Button(
            label="🎡 Spin!",
            style=discord.ButtonStyle.green,
            custom_id="spin_button"
        ))

@bot.command()
async def spinpanel(ctx):
    ...

intents = discord.Intents.all()


@bot.event
async def on_interaction(interaction):
    if interaction.data.get("custom_id") == "spin_button":
        reward = pick_reward()
        await interaction.response.send_message(
            f"🎉 {interaction.user.mention}, Kέρδισες: **{reward}**!",
            ephemeral=True
        )

# ---------------- PANEL COMMAND ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def spinpanel(ctx):
    if ctx.channel.id != PANEL_CHANNEL_ID:
        return

    embed = discord.Embed(
        title="🎡 Spin The Wheel",
        description="Πάτα το κουμπί για να γυρίσεις τον τροχό!. Για να δεις τι κέρδισες δες τα dms σου!",
        color=discord.Color.gold()
    )
    embed.set_image(url="https://i.imgur.com/Aq9eZcn.jpeg")

    await ctx.send(embed=embed, view=SpinButton())


# ---------------- SPIN COMMAND ----------------
@bot.command()
async def spin(ctx):

    # Έλεγχος καναλιού
    if ctx.channel.id != SPIN_CHANNEL_ID:
        return await ctx.reply(
            "❌ Μπορείς να κάνεις spin μόνο στο συγκεκριμένο κανάλι.",
            ephemeral=True
        )

    user = ctx.author
    now = datetime.utcnow()

    # Cooldown check
    if user.id in user_cooldowns:
        last_spin = user_cooldowns[user.id]
        diff = now - last_spin

        if diff < timedelta(hours=COOLDOWN_HOURS):
            remaining = timedelta(hours=COOLDOWN_HOURS) - diff
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)

            return await ctx.reply(
                f"⏳ Πρέπει να περιμένεις **{hours} ώρες και {minutes} λεπτά** πριν ξανακάνεις spin.",
                ephemeral=True
            )

    # Pick reward
    reward = pick_reward()
    user_cooldowns[user.id] = now

    # Send result ONLY to the user (ephemeral)
    await ctx.reply(
        f"🎉 **Κέρδισες:** {reward}",
        ephemeral=True
    )

    # Log στο log channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"🔔 {user} έκανε spin και κέρδισε: **{reward}**")


# Token από environment variable (DisCloud)
TOKEN = os.getenv("DISCORD_TOKEN")


bot.run(TOKEN)
