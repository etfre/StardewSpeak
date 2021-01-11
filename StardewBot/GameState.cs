using StardewValley;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewBot
{
    public static class GameState
    {

        public static object PlayerStatus() {
            string location = Game1.player.currentLocation?.Name;
            var player = Game1.player;
            var playerPosition = player.Position;
            var position = new { x = playerPosition.X, y = playerPosition.Y };
            var facingDirection = Game1.player.FacingDirection;
            var isMoving = Game1.player.isMoving();
            var status = new
            {
                location,
                position,
                tileX = player.getTileX(),
                tileY = player.getTileY(),
                facingDirection,
                isMoving
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
