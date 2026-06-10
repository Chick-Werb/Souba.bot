import discord
from discord import app_commands, ui
import os
import re
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

RANK_MULTIPLIERS = {
    'F': 2.45, 'E': 2.5, 'D': 2.55, 'C': 2.6,
    'B': 2.65, 'A': 2.7, 'S': 2.75
}

BLESSING_GEM_PRICE = 1070

def get_adjusted_multiplier(rank, current_level, is_special=False):
    base = RANK_MULTIPLIERS[rank]
    if is_special:
        return base - 0.10
    if current_level <= 3:
        return base + 0.05
    elif current_level <= 5:
        return base
    elif current_level <= 8:
        return base - 0.05
    else:
        return base - 0.10

@client.event
async def on_ready():
    print(f"ログイン成功！ あるけみすと装備相場Bot")
    print(f"名前: {client.user}")
    await tree.sync()

@tree.command(name="hello", description="挨拶＋宝石価格確認")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"ふむ、元気そうだな。何か食べていくか?\n"
        f"祝福の宝石現在価格は **{BLESSING_GEM_PRICE:,} マー**",
        ephemeral=True
    )

# ======================
# 係数調整ボタンView
# ======================
class CoefficientAdjustView(ui.View):
    def __init__(self, rank: str, base_price: int, target_plus: int, is_special: bool):
        super().__init__(timeout=180)
        self.rank = rank
        self.base_price = base_price
        self.target_plus = target_plus
        self.is_special = is_special
        self.extra_adjust = 0.0

    async def recalculate(self, interaction: discord.Interaction):
        def get_coeff(level):
            base = RANK_MULTIPLIERS[self.rank]
            if self.is_special:
                base -= 0.10
            if level <= 3:
                return base + 0.05 + self.extra_adjust
            elif level <= 5:
                return base + self.extra_adjust
            elif level <= 8:
                return base - 0.05 + self.extra_adjust
            else:
                return base - 0.10 + self.extra_adjust

        normal = float(self.base_price)
        for lv in range(1, self.target_plus + 1):
            normal *= get_coeff(lv)

        normal_price = round(normal)
        e_coeff = (normal_price / self.base_price) ** (1 / self.target_plus) if self.target_plus > 0 else 0

        await interaction.response.edit_message(
            content=f"**調整後: {self.rank}{self.base_price}+{self.target_plus}**\n"
                    f"→ **{normal_price:,} マー**\n"
                    f"**E係数: {e_coeff:.3f}** (調整: {self.extra_adjust:+.2f})",
            view=self
        )

    @ui.button(label="+0.05", style=discord.ButtonStyle.green)
    async def plus005(self, interaction: discord.Interaction, button: ui.Button):
        self.extra_adjust += 0.05
        await self.recalculate(interaction)

    @ui.button(label="-0.05", style=discord.ButtonStyle.red)
    async def minus005(self, interaction: discord.Interaction, button: ui.Button):
        self.extra_adjust -= 0.05
        await self.recalculate(interaction)

    @ui.button(label="+0.10", style=discord.ButtonStyle.green)
    async def plus01(self, interaction: discord.Interaction, button: ui.Button):
        self.extra_adjust += 0.10
        await self.recalculate(interaction)

    @ui.button(label="-0.10", style=discord.ButtonStyle.red)
    async def minus01(self, interaction: discord.Interaction, button: ui.Button):
        self.extra_adjust -= 0.10
        await self.recalculate(interaction)

    @ui.button(label="リセット", style=discord.ButtonStyle.gray, row=1)
    async def reset(self, interaction: discord.Interaction, button: ui.Button):
        self.extra_adjust = 0.0
        await self.recalculate(interaction)

# ======================
# メイン処理
# ======================
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip().upper()

    # 祝福価格変更（省略）

    clean_content = re.sub(r'\s+', '', content).replace('＋', '+')
    is_special = any(word in content for word in ["お得", "オトク", "おとく"])

    if len(clean_content) < 3 or '+' not in clean_content or clean_content[0] not in RANK_MULTIPLIERS:
        return

    try:
        rank = clean_content[0]
        rest = clean_content[1:]
        price_str, plus_str = rest.split('+', 1)
        base_price = int(price_str)
        target_plus = int(plus_str)

        if target_plus < 0:
            return

        # 計算処理（省略・前回と同じ）

        # ...（通常相場・宝石使用相場の計算はそのまま）...

        # 最終表示 + ボタン
        res = f"**{rank}{base_price}+{target_plus} の相場**\n"
        res += f"→ **{main_p:,} マー** （{main_t}）\n"
        if sub_p != main_p:
            res += f"　　（もう一方: {sub_p:,} マー）\n\n"

        res += "【詳細ステップ】\n" + "\n".join(steps) + "\n"
        res += f"最終: {main_p:,} マー　**E係数: {e_coeff:.3f}**"

        view = CoefficientAdjustView(rank, base_price, target_plus, is_special)
        await message.channel.send(res, view=view)

    except:
        return

# Flask部分はそのまま...