import discord
from discord import app_commands
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

# ======================
# E係数逆算関数（宝石コストを無視して理論倍率を求める）
# ======================
def calculate_e_coefficient(base_price, target_plus, final_price):
    if target_plus <= 0:
        return 0.0
    # 二分探索で係数を逆算
    low = 1.0
    high = 5.0
    for _ in range(50):  # 高精度
        mid = (low + high) / 2
        calculated = base_price
        for _ in range(target_plus):
            calculated *= mid
        if calculated < final_price:
            low = mid
        else:
            high = mid
    return (low + high) / 2

@client.event
async def on_ready():
    print(f"ログイン成功！ あるけみすと装備相場Bot")
    print(f"名前: {client.user}")
    await tree.sync()

@tree.command(name="hello", description="挨拶＋宝石価格確認")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"ふむ、元気そうだな。\n祝福の宝石現在価格は **{BLESSING_GEM_PRICE:,} マー**",
        ephemeral=True
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip().upper()

    if content.startswith("祝福"):
        # 祝福価格変更処理（省略）
        return

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

        # 通常相場
        normal = float(base_price)
        normal_steps = [f"+0: {base_price}"]
        for lv in range(1, target_plus + 1):
            coeff = get_adjusted_multiplier(rank, lv, is_special)
            normal *= coeff
            normal_steps.append(f"+{lv}: {normal:.0f} × {coeff:.2f} = {normal:.0f}")

        normal_price = round(normal)

        # 宝石使用相場
        gem = float(base_price)
        gem_steps = [f"+0: {base_price}"]
        gem_count = 0

        for lv in range(1, target_plus + 1):
            coeff = get_adjusted_multiplier(rank, lv, is_special)
            mul = gem * coeff

            if lv <= 3:
                gem_val = gem + BLESSING_GEM_PRICE
                chosen = min(mul, gem_val)
                if chosen == gem_val:
                    gem_count += 1
                    gem_steps.append(f"+{lv}: {gem:.0f} + {BLESSING_GEM_PRICE} = {chosen:.0f} (宝石)")
                else:
                    gem_steps.append(f"+{lv}: {gem:.0f} × {coeff:.2f} = {chosen:.0f}")
            else:
                chosen = mul
                gem_steps.append(f"+{lv}: {gem:.0f} × {coeff:.2f} = {chosen:.0f}")
            gem = chosen

        gem_price = round(gem)

        if gem_price < normal_price:
            main_p = gem_price
            main_t = f"宝石{gem_count}個使用"
            steps = gem_steps
        else:
            main_p = normal_price
            main_t = "通常"
            steps = normal_steps

       # ======================
# 祝福を考慮した理論E係数（二分探索）
# ======================
def calculate_theoretical_e_coeff(base_price, target_plus, final_price, bless_price=1070):
    if target_plus <= 0:
        return 0.0

    def calc_price(k):
        price = float(base_price)
        for i in range(1, target_plus + 1):
            if i <= 3:
                price = min(price * k, price + bless_price)
            else:
                price = price * k
        return price

    low = 1.0
    high = 4.0
    for _ in range(60):  # 高精度
        mid = (low + high) / 2
        if calc_price(mid) < final_price:
            low = mid
        else:
            high = mid
    return (low + high) / 2

        await message.channel.send(res)

    except Exception as e:
        print(f"計算エラー: {e}")
        return

# Flask部分
app = Flask(__name__)

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

Thread(target=run_flask).start()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("TOKEN未設定")
    exit(1)

client.run(TOKEN)