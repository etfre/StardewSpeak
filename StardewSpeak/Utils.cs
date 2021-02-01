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
using Microsoft.Xna.Framework.Input;

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

        public static object SerializedMenu(IClickableMenu menu) 
        {
            Point mousePosition = Game1.getMousePosition();
            return SerializedMenu(menu, mousePosition);
        }
        public static object SerializedMenu(IClickableMenu menu, Point mousePosition)
        {
            if (menu == null) return null;
            bool containsMouse = menu.isWithinBounds(mousePosition.X, mousePosition.Y);
            var menuBarObj = new
            {
                menu.xPositionOnScreen,
                containsMouse
            };
            dynamic menuTypeObj = new { };
            if (menu is ShopMenu)
            {
                var sm = menu as ShopMenu;
                menuTypeObj = new { menuType = "shopMenu", downArrow = SerializeClickableCmp(sm.downArrow, mousePosition) };
            }
            else if (menu is InventoryMenu) 
            {
                var im = menu as InventoryMenu;
                menuTypeObj = new 
                { 
                    menuType = "inventoryMenu",
                    inventory = im.inventory.Select(x => Utils.SerializeClickableCmp(x, mousePosition)),
                    im.rows,
                    im.capacity,
                };
            }
            else if (menu is ItemGrabMenu) 
            {
                var igm = menu as ItemGrabMenu;
                menuTypeObj = new
                {
                    menuType = "itemsToGrabMenu",
                    trashCan = Utils.SerializeClickableCmp(igm.trashCan, mousePosition),
                    inventoryMenu = Utils.SerializedMenu(igm.inventory, mousePosition),
                    itemsToGrabMenu = Utils.SerializedMenu(igm.ItemsToGrabMenu, mousePosition),
                    okButton = Utils.SerializeClickableCmp(igm.okButton, mousePosition),
                    organizeButton = Utils.SerializeClickableCmp(igm.organizeButton, mousePosition),
                };

            }

            return Utils.Merge(menuBarObj, menuTypeObj);
        }

        public static object SerializeClickableCmp(ClickableComponent cmp, Point mousePosition)
        {
            Rectangle bounds = cmp.bounds;
            bool containsMouse = cmp.containsPoint(mousePosition.X, mousePosition.Y);
            return new
            {
                bounds = new { x = bounds.X, y = bounds.Y, width = bounds.Width, height = bounds.Height },
                center = new List<int> { bounds.Center.X, bounds.Center.Y },
                cmp.name,
                containsMouse,
            };
        }
        public static void mouseClick() 
        {
        
        }

    }

}
