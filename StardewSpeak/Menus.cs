using Microsoft.Xna.Framework;
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
            _ = toCall.Invoke(null, new object[] { menuProps, menu, mousePosition }) as IDictionary<String, Object>;
            var serialized = new Dictionary<String, Object>();
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
            menu.animalsToPurchase = pam.animalsToPurchase;
            menu.okButton = pam.okButton;
            menu.namingAnimal = Utils.GetPrivateField(pam, "namingAnimal");
            if (menu.namingAnimal)
            {
                menu.randomButton = pam.randomButton;
                menu.doneNamingButton = pam.doneNamingButton;
            }
            menu.onFarm = Utils.GetPrivateField(pam, "onFarm");
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
