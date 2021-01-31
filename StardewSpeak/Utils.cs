using System;
using System.Collections.Generic;
using System.Dynamic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Xna.Framework;
using Newtonsoft.Json;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Menus;
using System;
using System.Runtime.InteropServices;

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
        public static dynamic Merge(object item1, object item2)
        {
            if (item1 == null || item2 == null)
                return item1 ?? item2 ?? new ExpandoObject();

            dynamic expando = new ExpandoObject();
            var result = expando as IDictionary<string, object>;
            foreach (System.Reflection.PropertyInfo fi in item1.GetType().GetProperties())
            {
                result[fi.Name] = fi.GetValue(item1, null);
            }
            foreach (System.Reflection.PropertyInfo fi in item2.GetType().GetProperties())
            {
                result[fi.Name] = fi.GetValue(item2, null);
            }
            return result;
        }
        public static object serializedMenu(IClickableMenu menu)
        {
            if (menu == null) return null;
            var menuBarObj = new
            {
                menu.xPositionOnScreen
            };
            dynamic menuTypeObj = new { };
            if (menu is ShopMenu)
            {
                var sm = menu as ShopMenu;
                menuTypeObj = new { downArrow = serializeClickableCmp(sm.downArrow) };
            }

            return Utils.Merge(menuBarObj, menuTypeObj);
        }

        public static object serializeClickableCmp(ClickableComponent cmp)
        {
            return new
            {
                cmp.bounds,
                center = new List<int> { cmp.bounds.Center.X, cmp.bounds.Center.Y },
                cmp.name,
            };
        }
        public static void mouseClick() 
        {
        
        }

    }

}
