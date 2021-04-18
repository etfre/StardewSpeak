using System;
using System.Collections.Generic;
using StardewValley;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using Microsoft.Xna.Framework;

namespace StardewSpeak
{

    public class EventHandler
    {
        public Dictionary<string, string> MapKeysToButtons;
        public List<string> buttons = new List<string> { "moveUpButton", "moveLeftButton", "moveDownButton", "moveRightButton" };
        private readonly IModHelper modHelper;
        private readonly SpeechEngine speechEngine;

        public EventHandler(IModHelper modHelper, SpeechEngine speechEngine) {
            PopulateMapKeysToButtons();
            this.modHelper = modHelper;
            this.speechEngine = speechEngine;
            this.RegisterEvents();
        }

        private void RegisterEvents() 
        {
            modHelper.Events.Input.ButtonPressed += this.OnButtonPressed;
        }

        private void OnButtonPressed(object sender, ButtonPressedEventArgs e)
        {
            // ignore if player hasn't loaded a save yet
            if (!Context.IsWorldReady) { return; }

            string key = e.Button.ToString();
            MapKeysToButtons.TryGetValue(key, out string button);
            speechEngine.SendEvent("KEY_PRESSED", new { key, button, isWorldReady = Context.IsWorldReady });
            string pressed = e.Button.ToString();
            //this.Monitor.Log($"{Game1.player.Name} presseddd {e.Button}.", LogLevel.Debug);
            //this.Monitor.Log(e.Button.ToString(), LogLevel.Debug);
            if (pressed == "R")
            {
                var menu = Game1.activeClickableMenu;
                var serializedMenu = Utils.SerializeMenu(Game1.activeClickableMenu);
                Utils.WriteJson("menu.json", serializedMenu);
            }
            else if (pressed == "K")
            {
                speechEngine.Exit();
            }
            else if (pressed == "L")
            {
                var player = Game1.player;
                var location = player.currentLocation;
                var mouseX = Game1.getMouseX();
                var mouseY = Game1.getMouseY();
                var point = Game1.currentCursorTile;
                var tileX = (int)point.X;
                var tileY = (int)point.Y;
                var vec = new Vector2(tileX, tileY);
                var viewport = Game1.viewport;
                ModEntry.Log($"Current tiles: x: {tileX}, y: {tileY}", LogLevel.Trace);
                ModEntry.Log($"Current mouse position: x: {mouseX}, y: {mouseY}", LogLevel.Trace);
                var tiles = Utils.VisibleTiles(Game1.player.currentLocation);

                var isOccupied = location.isTileOccupiedIgnoreFloors(vec);
                var rec = new xTile.Dimensions.Location(tileX, tileY);
                var t = player.CurrentTool;
                Utils.WriteJson("debris.json", location.debris.ToList());
                Utils.WriteJson("objects.json", location.Objects.Values.ToList());
                Utils.WriteJson("resourceClumps.json", location.resourceClumps.ToList());
                Utils.WriteJson("currentTool.json", player.CurrentTool);
                Utils.WriteJson("serializedResourceClumps.json", GameState.ResourceClumps());
                }
        }
        public void PopulateMapKeysToButtons() 
        {
            var map = new Dictionary<string, string>();
            foreach (var buttonName in buttons) 
            {
                AddButtonMap(map, buttonName);
            }
            MapKeysToButtons = map;
        }

        private void AddButtonMap(Dictionary<string, string> map, string buttonName) 
        {
            InputButton[] buttons = Utils.GetPrivateField(Game1.options, buttonName);
            foreach (var btn in buttons) 
            {
                map[btn.ToString()] = buttonName;
            }
        }

    }
}
