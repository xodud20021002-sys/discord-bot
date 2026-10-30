import os
import discord
import discord
from discord import app_commands
from datetime import datetime, timedelta, timezone

# 한국 시간대(KST, UTC+9) 설정
KST = timezone(timedelta(hours=9))
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

work_sessions = {}
attendance_records = {}

@client.event
async def on_ready():
    await tree.sync()
    print(f'로그인 완료: {client.user} (준비 완료!)')

@tree.command(name="출근", description="오늘의 출근을 기록합니다.")
async def clock_in(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = datetime.now(KST)
    
    if user_id in work_sessions:
        await interaction.response.send_message("⚠️ 이미 출근 상태입니다! 먼저 퇴근해주세요.", ephemeral=True)
        return
    
    work_sessions[user_id] = now
    time_str = now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
    
    if user_id not in attendance_records:
        attendance_records[user_id] = {"count": 0, "last_date": time_str}
    
    attendance_records[user_id]["count"] += 1
    attendance_records[user_id]["last_date"] = time_str
    
    total_count = attendance_records[user_id]["count"]
    
    await interaction.response.send_message(
        f"🟢 [출근 완료] {interaction.user.mention}님, 좋은 하루입니다!\n⏱️ 출근 시간: {time_str}\n📊 누적 출석 횟수: {total_count}회"
    )

@tree.command(name="퇴근", description="퇴근을 기록하고 총 근무 시간을 확인합니다.")
async def clock_out(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = datetime.now()
    
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

@tree.command(name="출석확인", description="나의 누적 출석 횟수와 최근 출근 기록을 확인합니다.")
async def check_attendance(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    if user_id not in attendance_records or attendance_records[user_id]["count"] == 0:
        await interaction.response.send_message("📊 아직 출석 기록이 없습니다. /출근 명령어를 사용해 보세요!", ephemeral=True)
        return
    
    c = attendance_records[user_id]["count"]
    d = attendance_records[user_id]["last_date"]
    
    await interaction.response.send_message(
        f"📋 [{interaction.user.name}님의 출석 현황]\n📊 누적 출석 횟수: {c}회\n🕒 최근 출석 일시: {d}",
        ephemeral=True
    )

client.run(os.getenv('TOKEN'))