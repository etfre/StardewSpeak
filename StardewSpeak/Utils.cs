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
using StardewValley.Tools;

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

        public static bool isOnScreen(Vector2 positionTile, int acceptableDistanceFromScreenNonTile, GameLocation location = null)
        {
            if (location != null && !location.Equals(Game1.currentLocation))
            {
                return false;
            }
            if (positionTile.X * 64 > Game1.viewport.X - acceptableDistanceFromScreenNonTile && positionTile.X * 64 < Game1.viewport.X + Game1.viewport.Width + acceptableDistanceFromScreenNonTile && positionTile.Y * 64 > Game1.viewport.Y - acceptableDistanceFromScreenNonTile)
            {
                return positionTile.Y * 64 < Game1.viewport.Y + Game1.viewport.Height + acceptableDistanceFromScreenNonTile;
            }
            return false;
        }

        public static bool GetClosestAnimal(Vector2 positionTile, int acceptableDistanceFromScreenNonTile, GameLocation location = null)
        {
            if (location != null && !location.Equals(Game1.currentLocation))
            {
                return false;
            }
            if (positionTile.X * 64 > Game1.viewport.X - acceptableDistanceFromScreenNonTile && positionTile.X * 64 < Game1.viewport.X + Game1.viewport.Width + acceptableDistanceFromScreenNonTile && positionTile.Y * 64 > Game1.viewport.Y - acceptableDistanceFromScreenNonTile)
            {
                return positionTile.Y * 64 < Game1.viewport.Y + Game1.viewport.Height + acceptableDistanceFromScreenNonTile;
            }
            return false;
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
            foreach (var kvp in IterObject(item1)) 
            {
                result[kvp.key] = kvp.value;
            }
            foreach (var kvp in IterObject(item2))
            {
                result[kvp.key] = kvp.value;
            }
            return result;
        }

        public static List<dynamic> IterObject(dynamic obj) {
            var items = new List<dynamic>();
            if (obj is ExpandoObject)
            {
                var exp = obj as ExpandoObject;
                foreach (var kvp in exp)
                {
                    items.Add(new { key = kvp.Key, value = kvp.Value });
                }
            }
            else 
            {
                foreach (System.Reflection.PropertyInfo fi in obj.GetType().GetProperties())
                {
                    items.Add(new { 
                        key = fi.Name, 
                        value = fi.GetValue(obj, null)
                    });
                }
            }
            return items;
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
                upperRightCloseButton = Utils.SerializeClickableCmp(menu.upperRightCloseButton, mousePosition),
                containsMouse,
                menuType = "unknown",
            };
            dynamic menuTypeObj = new { };
            if (menu is ShopMenu)
            {
                var sm = menu as ShopMenu;
                var forSale = sm.forSale.Select(x => Utils.SerializeItem((Item)x));
                var forSaleButtons = Utils.SerializeComponentList(sm.forSaleButtons, mousePosition);
                menuTypeObj = new
                {
                    menuType = "shopMenu",
                    forSale,
                    forSaleButtons,
                    sm.currentItemIndex,
                    inventory = SerializeMenu(sm.inventory),
                    upArrow = SerializeClickableCmp(sm.upArrow, mousePosition),
                    downArrow = SerializeClickableCmp(sm.downArrow, mousePosition),
                    scrollBar = SerializeClickableCmp(sm.scrollBar, mousePosition),
                };
            }
            if (menu is ProfileMenu)
            {
                var pm = menu as ProfileMenu;
                var clickableProfileItems = Utils.SerializeComponentList(pm.clickableProfileItems, mousePosition);
                menuTypeObj = new
                {
                    menuType = "profileMenu",
                    backButton = Utils.SerializeClickableCmp(pm.backButton, mousePosition),
                    forwardButton = Utils.SerializeClickableCmp(pm.forwardButton, mousePosition),
                    previousCharacterButton = Utils.SerializeClickableCmp(pm.previousCharacterButton, mousePosition),
                    nextCharacterButton = Utils.SerializeClickableCmp(pm.nextCharacterButton, mousePosition),
                    clickableProfileItems,
                    upArrow = SerializeClickableCmp(pm.upArrow, mousePosition),
                    downArrow = SerializeClickableCmp(pm.downArrow, mousePosition),
                };
            }
            else if (menu is DialogueBox)
            {
                var db = menu as DialogueBox;
                var responseCC = SerializeComponentList(db.responseCC, mousePosition);
                var responses = db.responses.Select(x => new { x.responseKey, x.responseText, x.hotkey }).ToList();
                menuTypeObj = new
                {
                    menuType = "dialogueBox",
                    responseCC,
                    responses,
                };
            }
            else if (menu is ShippingMenu)
            {
                var sm = menu as ShippingMenu;
                menuTypeObj = new
                {
                    menuType = "shippingMenu",
                    sm.itemsPerCategoryPage,
                    okButton = SerializeClickableCmp(sm.okButton, mousePosition),
                    sm.currentPage,
                };
            }
            else if (menu is MineElevatorMenu)
            {
                var mem = menu as MineElevatorMenu;
                var elevators = SerializeComponentList(mem.elevators, mousePosition);
                menuTypeObj = new
                {
                    menuType = "mineElevatorMenu",
                    elevators,
                };
            }
            else if (menu is LetterViewerMenu)
            {
                var lvm = menu as LetterViewerMenu;
                var itemsToGrab = SerializeComponentList(lvm.itemsToGrab, mousePosition);
                var acceptQuestButton = SerializeClickableCmp(lvm.acceptQuestButton, mousePosition);
                var backButton = SerializeClickableCmp(lvm.backButton, mousePosition);
                var forwardButton = SerializeClickableCmp(lvm.forwardButton, mousePosition);
                menuTypeObj = new
                {
                    menuType = "letterViewerMenu",
                    acceptQuestButton,
                    backButton,
                    forwardButton,
                    itemsToGrab,
                };
            }
            else if (menu is GameMenu) 
            {
                var gm = menu as GameMenu;
                var tabs = Utils.SerializeComponentList(gm.tabs, mousePosition);
                var currentPage = Page.SerializePage(gm.pages[gm.currentTab]);
                var pages = gm.pages.Select(x => Page.SerializePage(x)).ToList();
                menuTypeObj = new
                {
                    menuType = "gameMenu",
                    currentPage,
                    tabs,   
                };
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
                    buttons = SerializeComponentList(tm.buttons, mousePosition),
                    languageButton = SerializeClickableCmp(tm.languageButton, mousePosition),
                    skipButton = SerializeClickableCmp(tm.skipButton, mousePosition),
                    windowedButton = SerializeClickableCmp(tm.windowedButton, mousePosition),
                    subMenu = SerializeMenu(TitleMenu.subMenu),
                    backButton = SerializeClickableCmp(tm.backButton, mousePosition),
                };
                if (menuTypeObj.subMenu != null) 
                {
                 //   var backButton = SerializeClickableCmp(tm.backButton, mousePosition);
                   // menuTypeObj.submenu = Merge(menuTypeObj.submenu, new { backButton });
                }
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
                    genderButtons = SerializeComponentList(ccm.genderButtons, mousePosition),
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

        public static FarmAnimal FindAnimalByName(string name) 
        {
            var location = Game1.player.currentLocation;
            if (location is IAnimalLocation)
            {
                foreach (FarmAnimal animal in (location as IAnimalLocation).Animals.Values)
                {
                    if (name == animal.Name) return animal;
                }
            }
            return null;
        }
        public static object SerializeClickableCmp(ClickableComponent cmp, Point mousePosition)
        {
            if (cmp == null) return null;
            Rectangle bounds = cmp.bounds;
            bool containsMouse = cmp.containsPoint(mousePosition.X, mousePosition.Y);
            return new
            {
                type = "clickableComponent",
                bounds = new { x = bounds.X, y = bounds.Y, width = bounds.Width, height = bounds.Height },
                center = new List<int> { bounds.Center.X, bounds.Center.Y },
                cmp.name,
                containsMouse,
                cmp.visible,
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

        public static object SerializeItem(Item i) 
        {
            if (i == null) return null;
            var player = Game1.player;
            dynamic obj = new
            {
                netName = i.netName.Value,
                stack = i.Stack,
                displayName = i.DisplayName,
                name = i.Name,
                type = "",
                isTool = false,
            };
            if (i is Tool) 
            {
                var tool = i as Tool;
                obj = Utils.Merge(obj, new 
                { 
                    isTool = true,
                    upgradeLevel = tool.UpgradeLevel,
                    power = player.toolPower,
                    baseName = tool.BaseName,
                    inUse = player.UsingTool,
                });
            }
            if (i is MeleeWeapon)
            {
                var mw = i as MeleeWeapon;
                string type = mw.isScythe() ? "scythe" : "meleeWeapon";
                obj = Utils.Merge(obj, new { type });
            }
            else if (i is FishingRod)
            {
                var fr = i as FishingRod;
                obj = Utils.Merge(obj, new
                {
                    fr.castingPower,
                    fr.isNibbling,
                    fr.isFishing,
                    fr.isLostItem,
                    fr.isReeling,
                    fr.isTimingCast,
                    type = "fishingRod",
                });
            }
            else if (i is Axe)
            {
                obj = Utils.Merge(obj, new { type = "axe" });
            }
            else if (i is Pickaxe)
            {
                obj = Utils.Merge(obj, new { type = "pickaxe" });
            }
            else if (i is WateringCan)
            {
                obj = Utils.Merge(obj, new { type = "wateringCan" });
            }
            else if (i is Hoe) obj = Utils.Merge(obj, new { type = "hoe" });
            else if (i is MilkPail) obj = Utils.Merge(obj, new { type = "Milk Pail" });
            else if (i is Pan) obj = Utils.Merge(obj, new { type = "pan" });
            else if (i is Shears) obj = Utils.Merge(obj, new { type = "shears" });

            return obj;
        }
    }
}
