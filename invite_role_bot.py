# --- FLASK para manter o Render ativo ---
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está online!"

def run_flask():
    app.run(host="0.0.0.0", port=3000)

threading.Thread(target=run_flask).start()

# --- BOT DO DISCORD ---
import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_NAME = "autocop"
REQUIRED_INVITES = 3

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
invite_cache = {}

@bot.event
async def on_ready():
    print(f"✅ Bot ligado como {bot.user}")
    for guild in bot.guilds:
        invites = await guild.invites()
        invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}

@bot.event
async def on_member_join(member):
    guild = member.guild
    invites_before = invite_cache.get(guild.id, {})
    invites_after = await guild.invites()
    invite_cache[guild.id] = {invite.code: invite.uses for invite in invites_after}

    inviter = None
    for invite in invites_after:
        if invite.uses > invites_before.get(invite.code, 0):
            inviter = invite.inviter
            break

    if inviter:
        total = sum(i.uses for i in invites_after if i.inviter == inviter)
        if total >= REQUIRED_INVITES:
            role = discord.utils.get(guild.roles, name=ROLE_NAME)
            if role:
                member_to_edit = guild.get_member(inviter.id)
                if member_to_edit and role not in member_to_edit.roles:
                    await member_to_edit.add_roles(role)
                    print(f"{inviter} recebeu o cargo '{ROLE_NAME}'!")

# --- Comando !convites ---
@bot.command()
async def convites(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    guild = ctx.guild
    invites = await guild.invites()

    total = sum(i.uses for i in invites if i.inviter == membro)
    await ctx.send(f"🔗 {membro.mention} fez {total} convite(s) com sucesso.")

# --- Comando !topconvites ---
@bot.command()
async def topconvites(ctx):
    guild = ctx.guild
    invites = await guild.invites()

    ranking = {}
    for invite in invites:
        if invite.inviter not in ranking:
            ranking[invite.inviter] = 0
        ranking[invite.inviter] += invite.uses

    if not ranking:
        await ctx.send("Ninguém convidou ninguém ainda. 😢")
        return

    sorted_ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    mensagem = "🏆 **Top Convidadores:**\n\n"
    for i, (user, count) in enumerate(sorted_ranking[:10], start=1):
        mensagem += f"**{i}.** {user.mention} — `{count}` convite(s)\n"

    await ctx.send(mensagem)

bot.run(TOKEN)
