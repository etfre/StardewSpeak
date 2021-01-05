using System;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewModdingAPI.Utilities;
using StardewValley;

namespace StardewBot
{
    /// <summary>The mod entry point.</summary>
    public class ModEntry : Mod
    {
        internal static bool BotActive = false;
        SpeechEngine speechEngine;
        public static Action<string, LogLevel> log { get; private set; }

        /*********
** Public methods
*********/
        /// <summary>The mod entry point, called after the mod is first loaded.</summary>
        /// <param name="helper">Provides simplified APIs for writing mods.</param>
        public override void Entry(IModHelper helper)
        {
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
            helper.Events.GameLoop.UpdateTicked += GameLoop_UpdateTicked;
            ModEntry.log = this.Monitor.Log;
            this.speechEngine = new SpeechEngine();
        }


        public static void Log(string msg) {
            ModEntry.log(msg, LogLevel.Debug);
        }
        /*********
        ** Private methods
        *********/
        /// <summary>Raised after the player presses a button on the keyboard, controller, or mouse.</summary>
        /// <param name="sender">The event sender.</param>
        /// <param name="e">The event data.</param>
        private void OnButtonPressed(object sender, ButtonPressedEventArgs e)
        {
            // ignore if player hasn't loaded a save yet
            if (!Context.IsWorldReady) { }
                //return;
            // print button presses to the console window
            string pressed = e.Button.ToString();
            this.Monitor.Log($"{Game1.player.Name} presseddd {e.Button}.", LogLevel.Debug);
            this.Monitor.Log(e.Button.ToString(), LogLevel.Debug);
            if (pressed == "M") {
                var menu = Game1.activeClickableMenu;
            }
            if (pressed == "P")
            {
                this.Monitor.Log("pressed p");
                if (Routing.Ready)
                {
                    var route = Routing.GetRoute("HaleyHouse");
                    var watch = System.Diagnostics.Stopwatch.StartNew();
                    var targetTile = Game1.currentCursorTile;
                    var targetX = (int)targetTile.X;
                    var targetY = (int)targetTile.Y;

                    var path = Pathfinder.Pathfinder.FindPath(Game1.player.currentLocation, Game1.player.getTileX(), Game1.player.getTileY(), targetX, targetY, -1);
                    if (path == null)
                    {
                        ModEntry.Log("No path found");
                    }
                    else { 
                        foreach(var node in path) {
                            ModEntry.Log($"{node.Item1}, {node.Item2}");
                        }
                    }
                    watch.Stop();
                    var elapsedMs = watch.ElapsedMilliseconds;
                    ModEntry.Log($"{elapsedMs}");
                    }
                else
                {
                    Routing.Reset();
                }
                //Core.EquipToolIfOnHotbar("Pickaxe");
            }
            else if (pressed == "L")
            {
                var location = Game1.player.currentLocation;
                var point = Game1.currentCursorTile;
                var x = (int)point.X;
                var y = (int)point.Y;
                this.Monitor.Log($"Current Location: x: {x}, y: {y}", LogLevel.Debug);
                //var location = Game1.player.currentLocation;
                var v = new Vector2(x, y);
                var rec = new xTile.Dimensions.Location(x, y);
            }
        }
        private void GameLoop_UpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            //if (e.IsMultipleOf(30))
            //{
            //    var location = Game1.player.currentLocation;
            //    var point = Game1.currentCursorTile;
            //    var x = (int)point.X;
            //    var y = (int)point.Y;
            //    this.Monitor.Log($"Current Location: x: {x}, y: {y}", LogLevel.Debug);
            //}
        }
        private void ToggleBot()
        {
            BotActive = !BotActive;
            Monitor.Log("Toggled bot status. Bot is now " + (BotActive ? "ON." : "OFF."), LogLevel.Warn);
            if (!BotActive)
            {
                //Input.UninstallSimulator();
                Core.ReleaseKeys();
            }
            else
            {
                //Input.InstallSimulator();
                Core.Reset();
            }
        }
    }
}