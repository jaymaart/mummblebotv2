import asyncio
import datetime as dt
from typing import Optional

import disnake
import aiohttp
from disnake.ext import commands, tasks


class StreamScheduler(commands.Cog):
    """Stream schedule management and weekly updates."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.webhook_url = ""
        
        # Stream schedule configuration (PDT times)
        self.stream_schedule = {
            "Monday": {"start": "20:00", "end": "23:00", "day_offset": 0},  # Monday = 0
            "Wednesday": {"start": "20:00", "end": "23:00", "day_offset": 2},  # Wednesday = 2
            "Saturday": {"start": "22:00", "end": "01:00", "day_offset": 5},  # Saturday = 5
        }
        
        # Start the weekly update task
        self.weekly_schedule_update.start()
        
        # Send initial schedule when bot is ready
        self.send_initial_schedule.start()
    
    def cog_unload(self) -> None:
        """Clean up when the cog is unloaded."""
        self.weekly_schedule_update.cancel()
        self.send_initial_schedule.cancel()
    
    def get_next_stream_times(self) -> list[dict]:
        """Calculate the next occurrence of each stream day."""
        now = dt.datetime.now(dt.timezone.utc)
        pdt_tz = dt.timezone(dt.timedelta(hours=-7))  # PDT is UTC-7
        now_pdt = now.astimezone(pdt_tz)
        
        next_streams = []
        
        for day_name, schedule in self.stream_schedule.items():
            # Calculate days until next occurrence
            days_ahead = schedule["day_offset"] - now_pdt.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            # Calculate next occurrence date
            next_date = now_pdt + dt.timedelta(days=days_ahead)
            
            # Parse start and end times
            start_hour, start_minute = map(int, schedule["start"].split(":"))
            end_hour, end_minute = map(int, schedule["end"].split(":"))
            
            # Create datetime objects for start and end
            start_time = next_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end_time = next_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            # Handle Saturday's end time (crosses midnight)
            if day_name == "Saturday" and end_hour < start_hour:
                end_time += dt.timedelta(days=1)
            
            # Convert to UTC for Discord
            start_utc = start_time.astimezone(dt.timezone.utc)
            end_utc = end_time.astimezone(dt.timezone.utc)
            
            next_streams.append({
                "day": day_name,
                "start_time": start_utc,
                "end_time": end_utc,
                "start_unix": int(start_utc.timestamp()),
                "end_unix": int(end_utc.timestamp())
            })
        
        # Sort by start time
        next_streams.sort(key=lambda x: x["start_time"])
        return next_streams
    
    def create_schedule_embed(self) -> disnake.Embed:
        """Create a Discord embed with the stream schedule."""
        next_streams = self.get_next_stream_times()
        
        embed = disnake.Embed(
            title="📺 Weekly Stream Schedule",
            description="Here's when you can catch our streams this week!",
            color=0x5865F2,  # Discord Blurple
            timestamp=dt.datetime.now(dt.timezone.utc)
        )
        
        # Add stream information
        for stream in next_streams:
            start_time = stream["start_time"].strftime("%A, %B %d at %I:%M %p PDT")
            end_time = stream["end_time"].strftime("%I:%M %p PDT")
            
            # Format the time range
            time_range = f"<t:{stream['start_unix']}:F> - <t:{stream['end_unix']}:F>"
            
            embed.add_field(
                name=f"🎮 {stream['day']} Stream",
                value=f"**Time:** {time_range}\n",
                inline=False
            )
        
        # Add footer
        embed.set_footer(text="Schedule updates every Sunday • All times are in your local time")
        
        return embed
    
    async def send_schedule_webhook(self) -> None:
        """Send the schedule embed to the Discord webhook."""
        try:
            embed = self.create_schedule_embed()
            
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    "embeds": [embed.to_dict()],
                    "username": "Stream Scheduler",
                    "avatar_url": str(self.bot.user.display_avatar.url) if self.bot.user else None
                }
                
                async with session.post(self.webhook_url, json=webhook_data) as response:
                    if response.status == 204:
                        print(f"✅ Schedule sent successfully to webhook at {dt.datetime.now()}")
                    else:
                        print(f"❌ Failed to send webhook: {response.status}")
                        
        except Exception as e:
            print(f"❌ Error sending webhook: {e}")
    
    @tasks.loop(hours=168)  # 168 hours = 1 week
    async def weekly_schedule_update(self) -> None:
        """Update and send the schedule every week."""
        await self.send_schedule_webhook()
    
    @tasks.loop(count=1)  # Run only once
    async def send_initial_schedule(self) -> None:
        """Send the initial schedule when the bot starts up."""
        await self.bot.wait_until_ready()
        # Wait a few seconds to ensure everything is properly initialized
        await asyncio.sleep(5)
        print("🚀 Sending initial stream schedule...")
        await self.send_schedule_webhook()
        print("✅ Initial schedule sent successfully!")
    
    @weekly_schedule_update.before_loop
    async def before_weekly_update(self) -> None:
        """Wait until the next Sunday at 9 AM PDT before starting the loop."""
        await self.bot.wait_until_ready()

        now = dt.datetime.now(dt.timezone.utc)
        pdt_tz = dt.timezone(dt.timedelta(hours=-7))
        now_pdt = now.astimezone(pdt_tz)

        # Calculate next Sunday at 9 AM PDT (Sunday = 6)
        days_ahead = 6 - now_pdt.weekday()  # Sunday = 6
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7

        next_sunday = now_pdt + dt.timedelta(days=days_ahead)
        next_sunday = next_sunday.replace(hour=9, minute=0, second=0, microsecond=0)

        # Convert back to UTC
        next_sunday_utc = next_sunday.astimezone(dt.timezone.utc)

        # Calculate seconds to wait
        seconds_to_wait = (next_sunday_utc - now).total_seconds()

        if seconds_to_wait > 0:
            print(f"⏰ Waiting {seconds_to_wait/3600:.1f} hours until next Sunday 9 AM PDT for schedule update")
            await asyncio.sleep(seconds_to_wait)


def setup(bot: commands.Bot) -> None:
    """Load the StreamScheduler cog."""
    bot.add_cog(StreamScheduler(bot))