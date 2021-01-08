using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewBot
{
    public static class GameState
    {
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
