import os
import logging
import io
from typing import Optional
from datetime import datetime
import numpy as np

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ChatAction

from .vision_analyzer import ChartVisionAnalyzer
from .data_manager import HistoricalDataManager
from .pattern_matcher import PatternMatcher
from .result_analyzer import ResultAnalyzer

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 初始化组件
vision_analyzer = ChartVisionAnalyzer()
data_manager = HistoricalDataManager()
pattern_matcher = PatternMatcher()
result_analyzer = ResultAnalyzer()

# 用户会话数据
user_sessions = {}

class TelegramBotHandler:
    """Telegram Bot 处理器，支持交互式按键选择参数"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /start 命令"""
        user_id = update.effective_user.id
        user_sessions[user_id] = {
            'symbol': 'BTC/USDT',
            'timeframe': '4h',
            'top_n': 10,
            'min_similarity': 0.5
        }
        
        welcome_text = """
🤖 欢迎使用 K线模式匹配分析工具！

我可以帮您分析 K线图表，找到历史相似走势，并预测后续行情。

📊 使用方法：
1. 发送一张 K线截图
2. 选择交易对和时间周期
3. 我会分析并返回相似走势和概率

⚙️ 当前设置：
• 交易对：BTC/USDT
• 时间周期：4h
• 返回结果数：10
• 最低相似度：0.5

使用 /settings 修改设置
使用 /help 查看帮助
"""
        
        keyboard = [
            [KeyboardButton("📸 上传 K线截图")],
            [KeyboardButton("⚙️ 设置参数"), KeyboardButton("❓ 帮助")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /help 命令"""
        help_text = """
📖 使用帮助

🎯 功能说明：
• 上传 K线截图进行分析
• 自动识别币种和时间周期
• 在历史数据中找到相似走势
• 统计后续涨跌概率
• 计算平均收益和风险

⚙️ 参数设置：
• 交易对：选择要分析的交易对（如 BTC/USDT）
• 时间周期：选择 K线周期（5m, 15m, 30m, 1h, 4h, 1d）
• 返回结果数：返回前 N 个最相似的走势
• 最低相似度：过滤低于阈值的结果

📊 结果解读：
• 相似度：当前走势与历史走势的相似程度（0-100%）
• 上涨概率：历史相似走势中后续上涨的比例
• 平均收益：历史相似走势的平均后续收益率
• 置信度：预测的可信度（低/中/高）

⚠️ 免责声明：
本工具仅供参考，不构成投资建议。
历史模式不代表未来表现。
投资有风险，请谨慎决策。

💡 提示：
• 图表质量越好，识别准确度越高
• 包含指标线（EMA/MA）的图表识别效果更好
• 定期更新参数以适应市场变化
"""
        await update.message.reply_text(help_text)
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /settings 命令"""
        user_id = update.effective_user.id
        session = user_sessions.get(user_id, {})
        
        settings_text = f"""
⚙️ 当前参数设置：

交易对：{session.get('symbol', 'BTC/USDT')}
时间周期：{session.get('timeframe', '4h')}
返回结果数：{session.get('top_n', 10)}
最低相似度：{session.get('min_similarity', 0.5)}

请选择要修改的参数：
"""
        
        keyboard = [
            [
                InlineKeyboardButton("交易对", callback_data="set_symbol"),
                InlineKeyboardButton("时间周期", callback_data="set_timeframe")
            ],
            [
                InlineKeyboardButton("结果数", callback_data="set_top_n"),
                InlineKeyboardButton("相似度", callback_data="set_similarity")
            ],
            [InlineKeyboardButton("✅ 完成", callback_data="settings_done")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理按键回调"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if query.data == "set_symbol":
            keyboard = [
                [InlineKeyboardButton("BTC/USDT", callback_data="symbol_BTC/USDT"),
                 InlineKeyboardButton("ETH/USDT", callback_data="symbol_ETH/USDT")],
                [InlineKeyboardButton("BNB/USDT", callback_data="symbol_BNB/USDT"),
                 InlineKeyboardButton("SOL/USDT", callback_data="symbol_SOL/USDT")],
                [InlineKeyboardButton("XRP/USDT", callback_data="symbol_XRP/USDT"),
                 InlineKeyboardButton("ADA/USDT", callback_data="symbol_ADA/USDT")],
                [InlineKeyboardButton("🔙 返回", callback_data="back_settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("选择交易对：", reply_markup=reply_markup)
        
        elif query.data == "set_timeframe":
            keyboard = [
                [InlineKeyboardButton("5m", callback_data="tf_5m"),
                 InlineKeyboardButton("15m", callback_data="tf_15m"),
                 InlineKeyboardButton("30m", callback_data="tf_30m")],
                [InlineKeyboardButton("1h", callback_data="tf_1h"),
                 InlineKeyboardButton("4h", callback_data="tf_4h"),
                 InlineKeyboardButton("1d", callback_data="tf_1d")],
                [InlineKeyboardButton("🔙 返回", callback_data="back_settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("选择时间周期：", reply_markup=reply_markup)
        
        elif query.data == "set_top_n":
            keyboard = [
                [InlineKeyboardButton("5", callback_data="top_5"),
                 InlineKeyboardButton("10", callback_data="top_10"),
                 InlineKeyboardButton("15", callback_data="top_15")],
                [InlineKeyboardButton("20", callback_data="top_20"),
                 InlineKeyboardButton("30", callback_data="top_30")],
                [InlineKeyboardButton("🔙 返回", callback_data="back_settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("选择返回结果数：", reply_markup=reply_markup)
        
        elif query.data == "set_similarity":
            keyboard = [
                [InlineKeyboardButton("0.3", callback_data="sim_0.3"),
                 InlineKeyboardButton("0.5", callback_data="sim_0.5"),
                 InlineKeyboardButton("0.7", callback_data="sim_0.7")],
                [InlineKeyboardButton("0.8", callback_data="sim_0.8"),
                 InlineKeyboardButton("0.9", callback_data="sim_0.9")],
                [InlineKeyboardButton("🔙 返回", callback_data="back_settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("选择最低相似度：", reply_markup=reply_markup)
        
        elif query.data.startswith("symbol_"):
            symbol = query.data.replace("symbol_", "")
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            user_sessions[user_id]['symbol'] = symbol
            await query.answer(f"✅ 交易对已设置为 {symbol}")
            await query.edit_message_text(f"✅ 交易对已设置为 {symbol}\n\n使用 /settings 继续修改其他参数")
        
        elif query.data.startswith("tf_"):
            tf = query.data.replace("tf_", "")
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            user_sessions[user_id]['timeframe'] = tf
            await query.answer(f"✅ 时间周期已设置为 {tf}")
            await query.edit_message_text(f"✅ 时间周期已设置为 {tf}\n\n使用 /settings 继续修改其他参数")
        
        elif query.data.startswith("top_"):
            top_n = int(query.data.replace("top_", ""))
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            user_sessions[user_id]['top_n'] = top_n
            await query.answer(f"✅ 结果数已设置为 {top_n}")
            await query.edit_message_text(f"✅ 结果数已设置为 {top_n}\n\n使用 /settings 继续修改其他参数")
        
        elif query.data.startswith("sim_"):
            similarity = float(query.data.replace("sim_", ""))
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            user_sessions[user_id]['min_similarity'] = similarity
            await query.answer(f"✅ 相似度已设置为 {similarity}")
            await query.edit_message_text(f"✅ 相似度已设置为 {similarity}\n\n使用 /settings 继续修改其他参数")
        
        elif query.data == "back_settings":
            session = user_sessions.get(user_id, {})
            settings_text = f"""
⚙️ 当前参数设置：

交易对：{session.get('symbol', 'BTC/USDT')}
时间周期：{session.get('timeframe', '4h')}
返回结果数：{session.get('top_n', 10)}
最低相似度：{session.get('min_similarity', 0.5)}

请选择要修改的参数：
"""
            keyboard = [
                [
                    InlineKeyboardButton("交易对", callback_data="set_symbol"),
                    InlineKeyboardButton("时间周期", callback_data="set_timeframe")
                ],
                [
                    InlineKeyboardButton("结果数", callback_data="set_top_n"),
                    InlineKeyboardButton("相似度", callback_data="set_similarity")
                ],
                [InlineKeyboardButton("✅ 完成", callback_data="settings_done")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(settings_text, reply_markup=reply_markup)
        
        elif query.data == "settings_done":
            await query.answer("✅ 设置已保存")
            await query.edit_message_text("✅ 设置已保存。现在可以发送 K线截图进行分析。")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理用户发送的图片"""
        user_id = update.effective_user.id
        session = user_sessions.get(user_id, {
            'symbol': 'BTC/USDT',
            'timeframe': '4h',
            'top_n': 10,
            'min_similarity': 0.5
        })
        
        # 发送"正在分析"消息
        processing_msg = await update.message.reply_text("🔄 正在分析图表，请稍候...")
        
        try:
            # 显示"正在处理"状态
            await update.message.chat.send_action(ChatAction.TYPING)
            
            # 下载图片
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
            
            # 1. Vision 分析
            await processing_msg.edit_text("🔄 正在分析图表...")
            analysis = await vision_analyzer.analyze_chart(image_bytes=bytes(image_bytes))
            
            # 2. 确定交易对和时间周期
            symbol = session.get('symbol', 'BTC/USDT')
            timeframe = session.get('timeframe', '4h')
            
            # 3. 确保历史数据可用
            await processing_msg.edit_text("🔄 正在检索历史数据...")
            try:
                await data_manager.ensure_data(symbol, timeframe)
            except Exception as e:
                logger.error(f"Data sync error: {e}")
            
            # 4. 获取历史数据
            hist_ohlcv = data_manager.get_ohlcv(symbol, timeframe)
            hist_timestamps = data_manager.get_timestamps(symbol, timeframe)
            
            if len(hist_ohlcv) < 100:
                await processing_msg.edit_text(f"❌ 历史数据不足，无法进行分析。")
                return
            
            # 5. 模式匹配
            await processing_msg.edit_text("🔄 正在匹配模式...")
            query_seq = np.array(analysis.get("normalized_price_sequence", []))
            
            if len(query_seq) < 10:
                await processing_msg.edit_text("❌ 无法从图表中提取有效的价格序列。")
                return
            
            matches = pattern_matcher.find_similar_patterns(
                query_sequence=query_seq,
                historical_ohlcv=hist_ohlcv,
                historical_timestamps=hist_timestamps,
                top_n=session.get('top_n', 10),
                query_ema_state=analysis.get("indicators", {}).get("ema_arrangement", "tangled"),
                query_volume_pattern=analysis.get("indicators", {}).get("volume_pattern", "normal"),
                min_similarity=session.get('min_similarity', 0.5)
            )
            
            # 6. 结果分析
            summary = result_analyzer.summarize(matches)
            
            # 7. 格式化结果
            result_text = self._format_result(analysis, matches, summary, symbol, timeframe)
            
            await processing_msg.delete()
            await update.message.reply_text(result_text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            await processing_msg.edit_text(f"❌ 分析出错：{str(e)}")
    
    def _format_result(self, analysis, matches, summary, symbol, timeframe):
        """格式化分析结果为 Telegram 消息"""
        result = f"""
<b>📊 K线模式匹配结果</b>

<b>🎯 识别信息：</b>
• 交易对：<code>{symbol}</code>
• 时间周期：<code>{timeframe}</code>
• 识别置信度：{analysis.get('confidence', 50)}%

<b>📈 图表分析：</b>
• 趋势：{analysis.get('pattern', {}).get('trend', 'UNKNOWN')}
• 波动性：{analysis.get('pattern', {}).get('volatility', 'UNKNOWN')}
• EMA排列：{analysis.get('indicators', {}).get('ema_arrangement', 'UNKNOWN')}

<b>🔮 预测摘要：</b>
• 匹配数量：{summary.get('total_matches', 0)}个
• 平均相似度：{summary.get('avg_similarity', 0):.1%}
• 上涨概率：<b>{summary.get('bullish_probability', 0):.1%}</b>
• 平均收益：<b>{summary.get('avg_future_return', 0):.2%}</b>
• 置信度：<b>{summary.get('confidence', 'UNKNOWN')}</b>

<b>💡 建议：</b>
{summary.get('suggestion', '暂无建议')}

<b>📋 Top 3 匹配结果：</b>
"""
        
        for i, match in enumerate(matches[:3], 1):
            result += f"""
<b>{i}️⃣ 相似度 {match.get('similarity_score', 0):.1%}</b>
• 时间：{match.get('start_time', 'N/A')} ~ {match.get('end_time', 'N/A')}
• 后续走势：{'↑ 上涨' if match.get('future_trend') == 'up' else '↓ 下跌' if match.get('future_trend') == 'down' else '→ 横盘'}
• 后续收益：{match.get('future_return_1x', 0):.2%}
• 最大回撤：{match.get('future_max_drawdown', 0):.2%}
"""
        
        result += """

<b>⚠️ 免责声明：</b>
本工具仅供参考，不构成投资建议。
历史模式不代表未来表现。
投资有风险，请谨慎决策。
"""
        return result
    
    async def run(self):
        """启动 Telegram Bot"""
        self.application = Application.builder().token(self.token).build()
        
        # 添加处理器
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # 启动 Bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Telegram Bot started successfully")


async def main():
    """主函数"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    bot = TelegramBotHandler(token)
    await bot.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
