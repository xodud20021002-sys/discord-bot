import os
import discord
from discord import app_commands
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# 한국 시간(UTC + 9시간)을 계산하는 함수
def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

work_sessions = {}
attendance_records = {}  # 구조 변경: 사용자별로 출석 날짜(datetime 객체) 리스트를 저장

@client.event
async def on_ready():
    await tree.sync()
    print(f'로그인 완료: {client.user} (준비 완료!)')

@tree.command(name="출근", description="오늘의 출근을 기록합니다.")
async def clock_in(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = get_kst_now()
    
    if user_id in work_sessions:
        await interaction.response.send_message("⚠️ 이미 출근 상태입니다! 먼저 퇴근해주세요.", ephemeral=True)
        return
    
    work_sessions[user_id] = now
    
    # 사용자 기록 초기화 (없으면 리스트 생성)
    if user_id not in attendance_records:
        attendance_records[user_id] = []
    
    # 출석 시간(datetime)을 리스트에 추가
    attendance_records[user_id].append(now)
    
    total_count = len(attendance_records[user_id])
    time_str = now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
    
    await interaction.response.send_message(
        f"🟢 [출근 완료] {interaction.user.mention}님, 좋은 하루입니다!\n⏱️ 출근 시간: {time_str}\n📊 누적 출석 횟수: {total_count}회"
    )

@tree.command(name="퇴근", description="퇴근을 기록하고 총 근무 시간을 확인합니다.")
async def clock_out(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = get_kst_now()
    
    if user_id not in work_sessions:
        await interaction.response.send_message("⚠️ 아직 출근하지 않았거나 이미 퇴근하셨습니다!", ephemeral=True)
        return
    
    start_time = work_sessions.pop(user_id)
    duration = now - start_time
    
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    out_time_str = now.strftime("%H시 %M분 %S초")
    
    await interaction.response.send_message(
        f"🔴 [퇴근 완료] {interaction.user.mention}님, 수고하셨습니다!\n⏱️ 퇴근 시간: {out_time_str}\n⌛ 총 근무 시간: {hours}시간 {minutes}분 {seconds}초"
    )

@tree.command(name="출석확인", description="최근 7일간의 누적 출석 기록을 확인합니다.")
async def check_attendance(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    if user_id not in attendance_records or not attendance_records[user_id]:
        await interaction.response.send_message("📊 아직 출석 기록이 없습니다. /출근 명령어를 사용해 보세요!", ephemeral=True)
        return
    
    now = get_kst_now()
    seven_days_ago = now - timedelta(days=7)
    
    # 최근 7일 이내의 기록만 필터링
    recent_records = [t for t in attendance_records[user_id] if t >= seven_days_ago]
    
    total_count = len(attendance_records[user_id])
    
    if not recent_records:
        await interaction.response.send_message(f"📋 [{interaction.user.name}님의 출석 현황]\n📊 누적 출석 횟수: {total_count}회\n⚠️ 최근 7일 이내 출석 기록이 없습니다.", ephemeral=True)
        return
    
    # 보기 쉽게 문자열 목록으로 변환
    history_str = "\n".join([f"• {t.strftime('%Y년 %m월 %d일 %H시 %M분')}" for t in recent_records])
    
    await interaction.response.send_message(
        f"📋 [{interaction.user.name}님의 출석 현황 (최근 7일)]\n📊 총 누적 출석: {total_count}회\n\n🕒 **최근 7일간 출석 내역:**\n{history_str}",
        ephemeral=True
    )

# 렌더 포트 에러 방지용 가벼운 웹 서버 (Flask)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    client.run(os.getenv('TOKEN'))