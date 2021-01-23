using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace StardewBot
{
    public static class Utils
    {
        public static bool IsTileHoeable(GameLocation location, int x, int y) 
        {
            var tile = new Vector2(x, y);
            if (location.terrainFeatures.ContainsKey(tile) || location.objects.ContainsKey(tile)) return false;
            return location.doesTileHaveProperty((int)tile.X, (int)tile.Y, "Diggable", "Back") != null;
        }
    }
}
