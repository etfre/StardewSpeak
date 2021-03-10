using Microsoft.Xna.Framework;
using StardewValley;
using StardewValley.Menus;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web.UI.WebControls;

namespace StardewSpeak
{
    class Page
    {
        public static object SerializePage(dynamic obj) 
        {
            if (obj == null) return null;
            Point mousePosition = Game1.getMousePosition();
            if (obj is CataloguePage) return SerializeCataloguePage(obj);
            if (obj is CollectionsPage) return SerializeCollectionsPage(obj);
            if (obj is CraftingPage) return SerializeCraftingPage(obj);
            if (obj is InventoryPage) return SerializeInventoryPage(obj);
            if (obj is SocialPage) return SerializeSocialPage(obj, mousePosition);
            if (obj is ExitPage) return SerializeExitPage(obj);
            else return new { type = "unknown" };
        }
        public static object SerializeCataloguePage(CataloguePage page) 
        {
            return new { type = "cataloguePage" };
        }

        public static object SerializeSocialPage(SocialPage page, Point mousePosition)
        {
            ClickableTextureComponent downArrow = (ClickableTextureComponent)Utils.GetPrivateField(page, "downButton");
            ClickableTextureComponent upArrow = (ClickableTextureComponent)Utils.GetPrivateField(page, "upButton");
            var slotPosition = (int)Utils.GetPrivateField(page, "slotPosition");
            var sprites = ((List<ClickableTextureComponent>)Utils.GetPrivateField(page, "sprites")).Skip(slotPosition).Take(5).ToList();
            var characterSlots = Utils.SerializeComponentList(page.characterSlots, mousePosition).Skip(slotPosition).Take(5).ToList();
            return new {
                type = "socialPage",
                characterSlots,
                downArrow = Utils.SerializeClickableCmp(downArrow, mousePosition),
                //sprites = Utils.SerializeComponentList(sprites, mousePosition),
                upArrow = Utils.SerializeClickableCmp(upArrow, mousePosition),

            };
        }

        public static object SerializeInventoryPage(InventoryPage page)
        {
            Point mousePosition = Game1.getMousePosition();
            var equipmentIcons = Utils.SerializeComponentList(page.equipmentIcons, mousePosition);
            var upperRightCloseButton = Utils.SerializeClickableCmp(page.upperRightCloseButton, mousePosition);
            return new { 
                type = "inventoryPage",
                equipmentIcons,
                inventory = Utils.SerializeMenu(page.inventory, mousePosition),
                trashCan = Utils.SerializeClickableCmp(page.trashCan, mousePosition),
                upperRightCloseButton,
            };
        }
        public static object SerializeCraftingPage(CraftingPage page)
        {
            Point mousePosition = Game1.getMousePosition();
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
            return new
            {
                type = "craftingPage",
                currentCraftingPageIndex,
                downArrow = Utils.SerializeClickableCmp(page.downButton, mousePosition),
                currentRecipePage,
                inventory = Utils.SerializeMenu(page.inventory, mousePosition),
                trashCan = Utils.SerializeClickableCmp(page.trashCan, mousePosition),
                upArrow = Utils.SerializeClickableCmp(page.upButton, mousePosition),
            };
        }
        public static object SerializeCollectionsPage(CollectionsPage page)
        {
            Point mousePosition = Game1.getMousePosition();
            return new
            {
                type = "collectionsPage",
            };
        }

        public static object SerializeFarmInfoPage(FarmInfoPage page)
        {
            Point mousePosition = Game1.getMousePosition();
            var upperRightCloseButton = Utils.SerializeClickableCmp(page.upperRightCloseButton, mousePosition);
            return new
            {
                type = "farmInfoPage",
                upperRightCloseButton,
            };
        }
        public static object SerializeExitPage(ExitPage page)
        {
            Point mousePosition = Game1.getMousePosition();
            var exitToDesktop = Utils.SerializeClickableCmp(page.exitToDesktop, mousePosition);
            var exitToTitle = Utils.SerializeClickableCmp(page.exitToTitle, mousePosition);
            return new
            {
                type = "exitPage",
                exitToDesktop,
                exitToTitle,
            };
        }
    }
}
