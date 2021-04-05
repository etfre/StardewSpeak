using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Microsoft.Xna.Framework;
using Newtonsoft.Json;
using StardewSpeak.Pathfinder;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewModdingAPI.Utilities;
using StardewValley;
using StardewValley.Buildings;
using StardewValley.Tools;
using StardewValley.Menus;
using System.Reflection;
using System.Diagnostics;
using System.Threading.Tasks;

namespace StardewSpeak
{
    /// <summary>The mod entry point.</summary>
    public class ModEntry : Mod
    {
        internal static bool FeedLocation = false;
        SpeechEngine speechEngine;
        public static Action<string, LogLevel> log { get; private set; }
        public static Dictionary<string, Stream> Streams { get; set; } = new Dictionary<string, Stream>();

        public static IModHelper helper;

        /*********
** Public methods
*********/
        /// <summary>The mod entry point, called after the mod is first loaded.</summary>
        /// <param name="helper">Provides simplified APIs for writing mods.</param>
        public override void Entry(IModHelper helper)
        {
            ModEntry.helper = helper;
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
            helper.Events.Display.MenuChanged += this.OnMenuChanged;
            helper.Events.GameLoop.UpdateTicked += GameLoop_UpdateTicked;
            helper.Events.GameLoop.UpdateTicking += GameLoop_UpdateTicking;
            helper.Events.Player.Warped += this.OnWarped;
            helper.Events.World.TerrainFeatureListChanged += this.OnTerrainFeatureListChanged;
            helper.Events.World.ObjectListChanged += this.OnObjectListChanged;
            helper.Events.World.LargeTerrainFeatureListChanged += this.OnLargeTerrainFeatureListChanged;
            helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
            helper.Events.World.LocationListChanged += this.OnLocationListChanged;
            ModEntry.log = this.Monitor.Log;
            this.speechEngine = new SpeechEngine(OnSpeechEngineExited);
            this.speechEngine.LaunchProcess();
        }

        private void OnSpeechEngineExited(Process process, TaskCompletionSource<int> tcs) 
        {
            tcs.SetResult(process.ExitCode);
            ModEntry.Streams = new Dictionary<string, Stream>();
            Input.ClearHeld();
            Game1.addHUDMessage(new HUDMessage("Speech engine errored. Attempting to restart...", HUDMessage.error_type));
            ModEntry.log("Kaldi engine exited. Restarting in 5 seconds...", LogLevel.Debug);
            System.Threading.Thread.Sleep(5000);
            this.speechEngine.LaunchProcess();
        }

        public static void Log(string msg) {
            ModEntry.log(msg, LogLevel.Debug);
        }

        private void OnSaveLoaded(object sender, SaveLoadedEventArgs e) 
        {
            Routing.Reset();
        }

        private void OnLocationListChanged(object sender, LocationListChangedEventArgs e)
        {
            Routing.Reset();
        }


        private void OnWarped(object sender, WarpedEventArgs e)
        {
            long milliseconds = DateTime.Now.Ticks / TimeSpan.TicksPerMillisecond;
            var oldLocation = e.OldLocation.NameOrUniqueName;
            var newLocation = e.NewLocation.NameOrUniqueName;
            var warpEvent = new { timestamp = milliseconds, oldLocation, newLocation };
            foreach (var pair in ModEntry.Streams)
            {
                var id = pair.Key;
                var stream = pair.Value;
                if (stream.Name == "ON_WARPED") {
                    var message = new { stream_id = id, value = warpEvent };
                    this.speechEngine.SendMessage("STREAM_MESSAGE", message);
                    Log($"Warped to {e.NewLocation}");
                }
            }
            //this.speechEngine.SendEvent("ON_WARPED", warpEvent);
        }

        private void OnMenuChanged(object sender, MenuChangedEventArgs e) 
        {
            //e.OldMenu.
            var serializedEvent = new
            {
                oldMenu = Utils.SerializeMenu(e.OldMenu),
                newMenu = Utils.SerializeMenu(e.NewMenu),
            };
            this.MessageStreams("ON_MENU_CHANGED", serializedEvent);

        }

        private void MessageStreams(string streamName, dynamic messageValue) 
        {
            var messages = Stream.MessageStreams(ModEntry.Streams, streamName, messageValue);
            foreach (var message in messages) 
            {
                this.speechEngine.SendMessage("STREAM_MESSAGE", message);
            }
        }

        private void OnTerrainFeatureListChanged(object sender, TerrainFeatureListChangedEventArgs e)

        {
            var removed = e.Removed.Select(x => new { x.Value.currentTileLocation });
            var changedEvent = new { location = e.Location.NameOrUniqueName, removed };
            this.MessageStreams("ON_TERRAIN_FEATURE_LIST_CHANGED", changedEvent);
            Log($"ON_TERRAIN_FEATURE_LIST_CHANGED");
            //this.speechEngine.SendEvent("ON_WARPED", warpEvent);
        }


        private void OnObjectListChanged(object sender, ObjectListChangedEventArgs e)

        {
            var changedEvent = new { location = e.Location.NameOrUniqueName };
            this.MessageStreams("ON_OBJECT_LIST_CHANGED", changedEvent);
            Log($"ON_OBJECT_LIST_CHANGED");
            //this.speechEngine.SendEvent("ON_WARPED", warpEvent);
        }

        private void OnLargeTerrainFeatureListChanged(object sender, LargeTerrainFeatureListChangedEventArgs e) 
        {
            Log($"ON_LARGE_TERRAIN_FEATURE_LIST_CHANGED");

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
                Log($"Current tiles: x: {tileX}, y: {tileY}");
                Log($"Current mouse position: x: {mouseX}, y: {mouseY}");
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

        private void GameLoop_UpdateTicking(object sender, UpdateTickingEventArgs e)
        {
            foreach (var btn in Input.Held.Values) {
                Input.SetDown(btn);
            }
        }

        private void GameLoop_UpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            lock (speechEngine.RequestQueueLock) 
            {
                if (speechEngine.RequestQueue.Count > 0) // only handle 1 request per tick to minimize dropping frames
                {
                    var msg = speechEngine.RequestQueue.Dequeue();
                    speechEngine.RespondToMessage(msg);
                }
            }
            foreach (var pair in ModEntry.Streams)
            {
                var id = pair.Key;
                var stream = pair.Value;
                if (stream.Name != "UPDATE_TICKED" || !e.IsMultipleOf((uint)stream.Data.ticks)) continue;
                string state = stream.Data.state;
                string error = null;
                dynamic value;
                try
                {
                    value = Requests.HandleRequest(state);
                }
                catch (Exception exception)
                {
                    value = exception.ToString();
                    error = "STREAM_EXCEPTION";
                }
                var message = new { stream_id = id, value, error };
                this.speechEngine.SendMessage("STREAM_MESSAGE", message);
            }
        }
    }
}