using StardewModdingAPI.Events;
using StardewValley;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewBot
{

    public class Stream
    {
        public string Name;
        public string Id;
        public uint Ticks;
        public Stream(string name, string id, uint ticks) 
        {
            this.Name = name;
            this.Id = id;
            this.Ticks = ticks;
        }

        public object Gather(UpdateTickedEventArgs e)
        {
            switch (this.Name) 
            {
                case "PLAYER_STATUS":
                    string location = Game1.player.currentLocation?.Name;
                    var position = new { location = location, x = Game1.player.getTileX(), y = Game1.player.getTileY() };
                    var facingDirection = Game1.player.FacingDirection;
                    var isMoving = Game1.player.isMoving();
                    var status = new {
                        position = position,
                        facingDirection,
                        isMoving
                    };
                    return status;

            }
            return null;
        }

    }
}
