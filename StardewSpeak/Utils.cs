using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Xna.Framework;
using Newtonsoft.Json;
using StardewModdingAPI;
using StardewValley;

namespace StardewSpeak
{
    public static class Utils
    {
        public static bool IsTileHoeable(GameLocation location, int x, int y) 
        {
            var tile = new Vector2(x, y);
            if (location.terrainFeatures.ContainsKey(tile) || location.objects.ContainsKey(tile)) return false;
            return location.doesTileHaveProperty((int)tile.X, (int)tile.Y, "Diggable", "Back") != null;
        }
        public static void WriteJson(string fname, object obj)
        {
            var settings = new JsonSerializerSettings() { ReferenceLoopHandling = ReferenceLoopHandling.Ignore };
            settings.Error = (serializer, err) => err.ErrorContext.Handled = true;
            string objStr = JsonConvert.SerializeObject(obj, Formatting.None, settings);
            string path = @"C:\Program Files (x86)\GOG Galaxy\Games\Stardew Valley\Mods\StardewSpeak\StardewSpeak\lib\speech-client\debug\" + fname;
            using (var writetext = new StreamWriter(path))
            {
                writetext.WriteLine(objStr);
            }
        }
    }

}
