using Microsoft.Xna.Framework;
using StardewValley;
using StardewValley.Menus;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Dynamic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{
    public static class Menus
    {
        public static dynamic SerializeMenu(dynamic menu, Point mousePosition) 
        {
            if (menu == null) return null;
            string menuName = menu.GetType().Name;
            var toCall = Utils.GetStaticMethod(typeof(Menus), "Serialize_" + menuName);
            if (toCall == null) return null;
            bool containsMouse = menu.isWithinBounds(mousePosition.X, mousePosition.Y);
            dynamic menuProps = new ExpandoObject();
            menuProps.xPositionOnScreen = menu.xPositionOnScreen;
            menuProps.yPositionOnScreen = menu.yPositionOnScreen;
            menuProps.upperRightCloseButton = Utils.SerializeClickableCmp(menu.upperRightCloseButton, mousePosition);
            menuProps.containsMouse = containsMouse;
            menuProps.classType = menuName;
            _ = toCall.Invoke(null, new object[] { menuProps, menu, mousePosition }) as IDictionary<String, System.Object>;
            var serialized = new Dictionary<String, System.Object>();
            foreach (var property in menuProps)
            {
                serialized[property.Key] = SerializeValue(property.Value, mousePosition);
            }
            return serialized;
        }

        public static void Serialize_ShippingMenu(dynamic menu, ShippingMenu sm, Point cursorPosition)
        {
            int introTimer = Utils.GetPrivateField(sm, "introTimer");
            menu.menuType = "shippingMenu";
            if (sm.currentPage == -1)
            {
                if (introTimer <= 0)
                {
                    menu.okButton = sm.okButton;
                }
                menu.categories = sm.categories;
            }
            else 
            {
                menu.backButton = sm.backButton;
                menu.forwardButton = sm.forwardButton;
            }
        }

        public static void Serialize_PurchaseAnimalsMenu(dynamic menu, PurchaseAnimalsMenu pam, Point cursorPosition)
        {
            menu.menuType = "purchaseAnimalsMenu";
            menu.onFarm = Utils.GetPrivateField(pam, "onFarm");
            if (!menu.onFarm) menu.animalsToPurchase = pam.animalsToPurchase;
            menu.okButton = pam.okButton;
            menu.namingAnimal = Utils.GetPrivateField(pam, "namingAnimal");
            if (menu.namingAnimal)
            {
                menu.randomButton = pam.randomButton;
                menu.doneNamingButton = pam.doneNamingButton;
            }
        }

        public static void Serialize_BobberBar(dynamic menu, BobberBar bb, Point cursorPosition)
        {
            menu.menuType = "fishingMenu";
        }

        public static void Serialize_MineElevatorMenu(dynamic menu, MineElevatorMenu mem, Point cursorPosition)
        {
            menu.menuType = "mineElevatorMenu";
            menu.elevators = mem.elevators;
        }

        public static void Serialize_ItemGrabMenu(dynamic menu, ItemGrabMenu igm, Point cursorPosition)
        {
            var lastShippedHolder = igm.shippingBin ? igm.lastShippedHolder : null;
            var itemsToGrabMenu = igm.showReceivingMenu ? igm.ItemsToGrabMenu : null;
            menu.menuType = "itemsToGrabMenu";
            menu.trashCan = igm.trashCan;
            menu.inventoryMenu = igm.inventory;
            menu.itemsToGrabMenu = itemsToGrabMenu;
            menu.okButton = igm.okButton;
            menu.organizeButton = igm.organizeButton;
            menu.shippingBin = igm.shippingBin;
            menu.lastShippedHolder = lastShippedHolder;
            menu.colorPickerToggleButton = igm.colorPickerToggleButton;
            menu.discreteColorPickerCC = igm.discreteColorPickerCC;
            menu.fillStacksButton = igm.fillStacksButton;
            menu.junimoNoteIcon = igm.junimoNoteIcon;
        }

        public static void Serialize_GameMenu(dynamic menu, GameMenu gm, Point cursorPosition)
        {
            menu.menuType = "gameMenu";
            menu.currentPage = gm.pages[gm.currentTab];
            menu.tabs = gm.tabs;
        }
        public static void Serialize_SkillsPage(dynamic menu, SkillsPage page, Point mousePosition)
        {
            menu.menuType = "skillsPage";
            menu.skillAreas = page.skillAreas.Where(x => x.hoverText.Length > 0).ToList();
            menu.skillBars = page.skillBars.Where(x => x.hoverText.Length > 0 && !x.name.Equals("-1")).ToList();
            menu.specialItems = page.specialItems;
        }
        public static void Serialize_CataloguePage(dynamic menu, CataloguePage page, Point mousePosition)
        {
            menu.menuType = "cataloguePage";
        }

        public static void Serialize_SocialPage(dynamic menu, SocialPage page, Point mousePosition)
        {
            menu.menuType = "socialPage";
            menu.downArrow = (ClickableTextureComponent)Utils.GetPrivateField(page, "downButton");
            menu.upArrow = (ClickableTextureComponent)Utils.GetPrivateField(page, "upButton");
            menu.slotPosition = (int)Utils.GetPrivateField(page, "slotPosition");
            //menu.sprites = ((List<ClickableTextureComponent>)Utils.GetPrivateField(page, "sprites")).Skip(menu.slotPosition).Take(5).ToList();
            menu.characterSlots = page.characterSlots.GetRange(menu.slotPosition, 5);
        }

        public static void Serialize_InventoryPage(dynamic menu, InventoryPage page, Point mousePosition)
        {
            var equipmentIcons = Utils.SerializeComponentList(page.equipmentIcons, mousePosition);
            menu.menuType = "inventoryPage";
            menu.equipmentIcons = page.equipmentIcons;
            menu.inventory = page.inventory;
            menu.trashCan = page.trashCan;
        }
        public static void Serialize_CraftingPage(dynamic menu, CraftingPage page, Point mousePosition)
        {
            int currentCraftingPageIndex = (int)Utils.GetPrivateField(page, "currentCraftingPage");
            var recipePage = page.pagesOfCraftingRecipes[currentCraftingPageIndex];
            var currentRecipePage = new List<List<dynamic>>();
            foreach (var pair in recipePage)
            {
                var r = pair.Value;
                var cmp = Utils.SerializeClickableCmp(pair.Key, mousePosition);
                var recipe = new { r.name, r.description, itemType = r.ItemType };
                currentRecipePage.Add(new List<dynamic> { cmp, recipe });
            }
            menu.menuType = "craftingPage";
            menu.currentCraftingPageIndex = currentCraftingPageIndex;
            menu.downArrow = page.downButton;
            menu.currentRecipePage = currentRecipePage;
            menu.inventory = page.inventory;
            menu.trashCan = page.trashCan;
            menu.upArrow = page.upButton;
        }
        public static void Serialize_CollectionsPage(dynamic menu, CollectionsPage page, Point mousePosition)
        {
            menu.menuType = "collectionsPage";
            int currentPageNumber = page.currentPage;
            var currentCollection = page.collections[page.currentTab];
            var currentPage = currentCollection[currentPageNumber];
            if (currentPageNumber > 0) menu.backButton = page.backButton;
            if (currentPageNumber < currentCollection.Count - 1) menu.forwardButton = page.forwardButton;
            menu.currentPage = currentPage;
            menu.tabs = page.sideTabs.Values.ToList();
        }

        public static void Serialize_FarmInfoPage(dynamic menu, FarmInfoPage page, Point mousePosition)
        {
            menu.menuType = "farmInfoPage";
        }
        public static void Serialize_ExitPage(dynamic menu, ExitPage page, Point mousePosition)
        {
            menu.menuType = "exitPage";
            menu.exitToTitle = page.exitToDesktop;
            menu.exitToTitle = page.exitToTitle;
        }

    public static dynamic SerializeValue(dynamic val, Point cursorPosition)
        {
            if (val is ClickableComponent || val is ClickableTextureComponent)
            {
                return Utils.SerializeClickableCmp(val, cursorPosition);
            }
            if (val is IClickableMenu) 
            {
                return Utils.SerializeMenu(val);
            }
            if (val is IList && val.GetType().IsGenericType)
            {
                var listVal = new List<dynamic>();
                foreach (var item in val)
                {
                    listVal.Add(SerializeValue(item, cursorPosition));
                }
                return listVal;
            }
            return val;
        }

    }
}
