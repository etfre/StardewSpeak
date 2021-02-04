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
using System.Runtime.InteropServices;
using Microsoft.Xna.Framework.Input;
using System.Reflection;
using StardewValley.TerrainFeatures;

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

        public static object SerializeMenu(IClickableMenu menu)
        {
            Point mousePosition = Game1.getMousePosition();
            return SerializeMenu(menu, mousePosition);
        }
        public static object SerializeMenu(IClickableMenu menu, Point mousePosition)
        {
            if (menu == null) return null;
            bool containsMouse = menu.isWithinBounds(mousePosition.X, mousePosition.Y);
            var menuBarObj = new
            {
                menu.xPositionOnScreen,
                allClickableComponents = SerializeComponentList(menu.allClickableComponents, mousePosition),
                menu.upperRightCloseButton,
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
                    inventory = SerializeComponentList(im.inventory, mousePosition),
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
                    inventoryMenu = Utils.SerializeMenu(igm.inventory, mousePosition),
                    itemsToGrabMenu = Utils.SerializeMenu(igm.ItemsToGrabMenu, mousePosition),
                    okButton = Utils.SerializeClickableCmp(igm.okButton, mousePosition),
                    organizeButton = Utils.SerializeClickableCmp(igm.organizeButton, mousePosition),
                };

            }
            else if (menu is TitleMenu)
            {
                var tm = menu as TitleMenu;
                menuTypeObj = new
                {
                    menuType = "titleMenu",
                    backButton = SerializeClickableCmp(tm.backButton, mousePosition),
                    buttons = SerializeComponentList(tm.buttons, mousePosition),
                    languageButton = SerializeClickableCmp(tm.languageButton, mousePosition),
                    skipButton = SerializeClickableCmp(tm.skipButton, mousePosition),
                    windowedButton = SerializeClickableCmp(tm.windowedButton, mousePosition),
                    subMenu = SerializeMenu(TitleMenu.subMenu),
                };
            }
            else if (menu is CharacterCustomization)
            {
                var ccm = menu as CharacterCustomization;
                menuTypeObj = new
                {
                    menuType = "characterCustomizationMenu",
                    backButton = SerializeClickableCmp(ccm.backButton, mousePosition),
                    cabinLayoutButtons = SerializeComponentList(ccm.cabinLayoutButtons, mousePosition),
                    farmTypeButtons = SerializeComponentList(ccm.farmTypeButtons, mousePosition),
                    favThingBoxCC = SerializeClickableCmp(ccm.favThingBoxCC, mousePosition),
                    farmnameBoxCC = SerializeClickableCmp(ccm.farmnameBoxCC, mousePosition),
                    leftSelectionButtons = SerializeComponentList(ccm.leftSelectionButtons, mousePosition),
                    nameBoxCC = SerializeClickableCmp(ccm.nameBoxCC, mousePosition),
                    okButton = SerializeClickableCmp(ccm.okButton, mousePosition),
                    petButtons = SerializeComponentList(ccm.petButtons, mousePosition),
                    randomButton = SerializeClickableCmp(ccm.randomButton, mousePosition),
                    rightSelectionButtons = SerializeComponentList(ccm.rightSelectionButtons, mousePosition),
                    skipIntroButton = SerializeClickableCmp(ccm.skipIntroButton, mousePosition),
                };
            }
            else if (menu is LoadGameMenu)
            {
                var lgm = menu as LoadGameMenu;
                int currentItemIndex = (int)GetPrivateField(lgm, "currentItemIndex");
                menuTypeObj = new
                {
                    menuType = "loadGameMenu",
                    currentItemIndex,
                    deleteButtons = SerializeComponentList(lgm.deleteButtons, mousePosition),
                    slotButtons = SerializeComponentList(lgm.slotButtons, mousePosition),
                    upArrow = SerializeClickableCmp(lgm.upArrow, mousePosition),
                    downArrow = SerializeClickableCmp(lgm.downArrow, mousePosition),
                    lgm.deleteConfirmationScreen,
                };
            }

            return Utils.Merge(menuBarObj, menuTypeObj);
        }

        public static List<object> SerializeComponentList(List<ClickableComponent> components, Point mousePosition)
        {
            return components?.Select(x => SerializeClickableCmp(x, mousePosition)).ToList();
        }

        public static List<object> SerializeComponentList(List<ClickableTextureComponent> components, Point mousePosition)
        {
            return components?.Select(x => SerializeClickableCmp(x, mousePosition)).ToList();
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
        public static object GetPrivateField(object obj, string fieldName)
        {
            var value = obj.GetType().GetField(fieldName, BindingFlags.NonPublic | BindingFlags.Instance)?.GetValue(obj);
            return value;
        }

        public static void SetPrivateField(object obj, string fieldName, dynamic value)
        {
            var field = obj.GetType().GetField(fieldName, BindingFlags.NonPublic | BindingFlags.Instance);
            if (field != null) field.SetValue(obj, value);
        }

        public static bool CanPlantOnHoeDirt(HoeDirt hd)
        {
            Item currentItem = Game1.player.ActiveObject;
            if (currentItem == null) return false;
            bool equippedFertilizer = currentItem.Category == -19;
            // canPlantThisSeedHere fertilizer test doesn't account for existing crops
            if (equippedFertilizer)
            {
                int fertilizer = hd.fertilizer.Value;
                bool emptyOrUngrownCrop = hd.crop == null || hd.crop.currentPhase == 0;
                return emptyOrUngrownCrop && fertilizer == 0;
            }
            int objIndex = currentItem.ParentSheetIndex;
            Vector2 tileLocation = hd.currentTileLocation;
            int tileX = (int)tileLocation.X;
            int tileY = (int)tileLocation.Y;
            return hd.canPlantThisSeedHere(objIndex, tileX, tileY, false);
        }
    }
}
