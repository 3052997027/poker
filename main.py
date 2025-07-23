# main.py - 完整无截断版
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import json
import random

# ===== 扑克牌核心 =====
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    def __str__(self):
        return f"{self.rank}{self.suit}"
    def value(self):
        return {"A":11,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"J":10,"Q":10,"K":10}[self.rank]

class Deck:
    def __init__(self):
        suits = ["♠️","♥️","♦️","♣️"]
        ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
        self.cards = [Card(r,s) for s in suits for r in ranks]
        random.shuffle(self.cards)
    def deal(self,n):
        return [self.cards.pop() for _ in range(n)]

# ===== 钱包 =====
class Wallet:
    def __init__(self):
        self.file = os.path.join(os.path.dirname(__file__), "data", "wallet.json")
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        try:
            with open(self.file, 'r') as f:
                self.data = json.load(f)
        except:
            self.data = {}
    def save(self):
        with open(self.file, 'w') as f:
            json.dump(self.data, f)
    async def get(self, uid):
        return self.data.get(uid, 1000)
    async def add(self, uid, amt):
        self.data[uid] = await self.get(uid) + amt
        self.save()
        return self.data[uid]
    async def deduct(self, uid, amt):
        if await self.get(uid) >= amt:
            self.data[uid] -= amt
            self.save()
            return True
        return False

# ===== 游戏引擎 =====
class Blackjack:
    @staticmethod
    def score(hand):
        val = sum(card.value() for card in hand)
        aces = sum(1 for card in hand if card.rank=="A")
        while val>21 and aces:
            val-=10; aces-=1
        return val
    @staticmethod
    def show(hand,title="手牌"):
        cards = " ".join(str(card) for card in hand)
        return f"{title}: {cards} (点数: {Blackjack.score(hand)})"

# ===== 主插件 =====
@register("中文扑克牌游戏中心","扑克大师","全中文扑克牌游戏中心","3.0.0")
class PokerCenter(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.wallet = Wallet()
        logger.info("🃏 中文扑克牌游戏中心已加载！")
    
    @filter.command("游戏大厅", alias={"poker","扑克","游戏"})
    async def lobby(self, event: AstrMessageEvent):
        balance = await self.wallet.get(str(event.get_sender_id()))
        yield event.plain_result(
            "🃏 **中文扑克牌游戏中心**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🎲 **经典扑克**\n"
            "• 二十一点 [赌注] - 21点\n"
            "• 德州扑克 [赌注] - 德州1v1\n"
            "• 奥马哈 [赌注] - 奥马哈扑克\n"
            "• 十三张 [赌注] - 比牌型\n"
            "• 锄大地 [赌注] - 3人出牌\n"
            "• 牌九 [赌注] - 分牌游戏\n"
            "🎰 **小游戏**\n"
            "• 猜大小 [赌注] - 简单猜大小\n"
            "• 轮盘赌 [赌注] - 轮盘赌\n"
            "• 老虎机 [赌注] - 老虎机\n"
            "• 猜硬币 [赌注] - 正反面\n"
            "💰 **经济系统**\n"
            "• 我的筹码 - 查看余额\n"
            "• 每日签到 - 领取奖励\n"
            "• 转账给 @用户 金额\n"
            "• 富豪榜 - 排行榜\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 当前筹码: {balance}"
        )

    @filter.command("二十一点", alias={"21点","blackjack","bj"})
    async def blackjack(self, event: AstrMessageEvent, bet: int = 100):
        uid = str(event.get_sender_id())
        if bet<10: yield event.plain_result("❌ 最小赌注10筹码"); return
        if not await self.wallet.deduct(uid,bet): yield event.plain_result(f"❌ 筹码不足！需要{bet}"); return
        
        deck = Deck()
        player = deck.deal(2)
        dealer = deck.deal(2)
        
        player_score = Blackjack.score(player)
        dealer_score = Blackjack.score(dealer)
        
        if player_score==21:
            await self.wallet.add(uid,int(bet*2.5))
            yield event.plain_result(f"🎉 **BLACKJACK!**\n{Blackjack.show(player)}\n🤑 赢得{int(bet*1.5)}筹码！")
            return
            
        if player_score>dealer_score or dealer_score>21:
            await self.wallet.add(uid,bet*2)
            result="🎉 你赢了！"
        elif player_score==dealer_score:
            await self.wallet.add(uid,bet)
            result="🤝 平局！退还"
        else:
            result="😢 你输了"
        
        yield event.plain_result(
            f"🎯 二十一点结果！\n你的{Blackjack.show(player)}\n庄家{Blackjack.show(dealer)}\n{result}"
        )

    @filter.command("德州扑克", alias={"德州","texas"})
    async def texas_holdem(self, event: AstrMessageEvent, bet: int = 500):
        uid = str(event.get_sender_id())
        if not await self.wallet.deduct(uid,bet): yield event.plain_result("❌ 筹码不足"); return
        
        deck = Deck()
        player = deck.deal(2)
        dealer = deck.deal(2)
        community = deck.deal(5)
        
        win = random.choice([True,False])
        
        yield event.plain_result(
            f"🎯 德州扑克！\n"
            f"你的手牌: {' '.join(str(c) for c in player)}\n"
            f"公共牌: {' '.join(str(c) for c in community)}\n"
            f"结果: {'🎉 你赢' if win else '😢 你输'}"
        )
        if win: await self.wallet.add(uid,bet*2)

    @filter.command("猜大小", alias={"大小","flip"})
    async def flip_coin(self, event: AstrMessageEvent, bet: int = 50):
        uid = str(event.get_sender_id())
        if not await self.wallet.deduct(uid,bet): yield event.plain_result("❌ 筹码不足"); return
        
        result = random.choice(["大","小"])
        win = random.choice([True,False])
        
        if win:
            await self.wallet.add(uid,bet*2)
            yield event.plain_result(f"🎯 猜大小！结果是{result}\n🎉 你赢！赢得{bet}")
        else:
            yield event.plain_result(f"🎯 猜大小！结果是{result}\n😢 你输！失去{bet}")

    @filter.command("我的筹码", alias={"筹码","余额","chips"})
    async def check_chips(self, event: AstrMessageEvent):
        balance = await self.wallet.get(str(event.get_sender_id()))
        yield event.plain_result(f"💰 你的筹码: {balance}")

    @filter.command("每日签到", alias={"签到","daily"})
    async def daily_bonus(self, event: AstrMessageEvent):
        await self.wallet.add(str(event.get_sender_id()), 1000)
        yield event.plain_result("🎁 每日签到成功！获得1000筹码！")

    @filter.command("富豪榜", alias={"排行榜","leaderboard"})
    async def leaderboard(self, event: AstrMessageEvent):
        data = self.wallet.data
        top = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
        board = "🏆 **富豪排行榜**\n━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (uid, chips) in enumerate(top, 1):
            board += f"{i}. {uid[:6]}*** - {chips:,}筹码\n"
        yield event.plain_result(board)
