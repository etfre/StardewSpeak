using StardewValley;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace StardewBot
{
    public static class GameState
    {
        public static object LastWarp = null;

        public static object PlayerStatus() {
            var player = Game1.player;
            string location = player.currentLocation?.Name;
            var playerPosition = player.Position;
            var position = new { x = playerPosition.X, y = playerPosition.Y };
            var facingDirection = player.FacingDirection;
            var isMoving = player.isMoving();
            var status = new
            {
                location,
                position,
                tileX = player.getTileX(),
                tileY = player.getTileY(),
                facingDirection,
                isMoving,
                lastWarp = LastWarp
            };
            return status;
        }

        public static object GameValues() 
        {
            var values = new
            {
                tilesize = Game1.tileSize
                //x = Game1.
            };
            return values;
        }

        public static Position PlayerPosition { get; set; }
    }
    public class Position {
        public string location { get; set; }
        public int x { get; set; }
        public int y { get; set; }
        
        public Position(string location, int x, int y) {
            this.location = location;
            this.x = x;
            this.y = y;
        }
    }
}
