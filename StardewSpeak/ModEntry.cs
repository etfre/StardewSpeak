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
using System.Threading;
using System.Collections.Concurrent;

namespace StardewSpeak
{
    /// <summary>The mod entry point.</summary>
    public class ModEntry : Mod
    {
        internal static bool FeedLocation = false;
        SpeechEngine speechEngine;
        EventHandler eventHandler;

        public static Action<string, LogLevel> log { get; private set; }
        public static Dictionary<string, Stream> Streams { get; set; } = new Dictionary<string, Stream>();
        public static List<InputButton[]> ButtonsToCheck = new List<InputButton[]>();
        public static IModHelper helper;
        public static HUDMessage QueuedMessage = null;
        public static dynamic lastGameEvent = null;

        /*********
** Public methods
*********/
        /// <summary>The mod entry point, called after the mod is first loaded.</summary>
        /// <param name="helper">Provides simplified APIs for writing mods.</param>
        public override void Entry(IModHelper helper)
        {
            ModEntry.helper = helper;

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
            this.eventHandler = new EventHandler(helper, this.speechEngine);
            helper.ConsoleCommands.Add("mimic", "Mimic speech recognition after three second delay, e.g. \"mimic load game\"", Command_MimicSpeech);
        }

        private void Command_MimicSpeech(string name, string[] actions) 
        {
            if (actions.Length == 0) return;
            {
                string said = String.Join(" ", actions);
                this.speechEngine.SendEvent("SPEECH_MIMICKED", new { said });
            }
        }

        private void OnSpeechEngineExited(Process process, TaskCompletionSource<int> tcs) 
        {
            ModEntry.Streams = new Dictionary<string, Stream>();
            Input.ClearHeld();
            Game1.addHUDMessage(new HUDMessage("Speech engine errored. Attempting to restart...", HUDMessage.error_type));
            ModEntry.log("Kaldi engine exited. Restarting in 5 seconds...", LogLevel.Debug);
            System.Threading.Thread.Sleep(5000);
            this.speechEngine.LaunchProcess();
        }

        public static void Log(string msg, LogLevel level) {
            ModEntry.log(msg, level);
        }

        private void OnSaveLoaded(object sender, SaveLoadedEventArgs e) 
        {
            if (QueuedMessage != null) 
            {
                Game1.addHUDMessage(QueuedMessage);
                QueuedMessage = null;
            }
            Routing.Reset();
            this.speechEngine.SendEvent("SAVE_LOADED");
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
                }
            }
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
        }


        private void OnObjectListChanged(object sender, ObjectListChangedEventArgs e)

        {
            var changedEvent = new { location = e.Location.NameOrUniqueName };
            this.MessageStreams("ON_OBJECT_LIST_CHANGED", changedEvent);
        }

        private void OnLargeTerrainFeatureListChanged(object sender, LargeTerrainFeatureListChangedEventArgs e) 
        {

        }
        private void RespondToQueuedRequests(ConcurrentQueue<dynamic> queue, int timeLimit = 5) 
        {
            var sw = Stopwatch.StartNew();
            while (!queue.IsEmpty)
            {
                if (!queue.TryDequeue(out dynamic msg)) continue;
                speechEngine.RespondToMessage(msg);
                if (sw.ElapsedMilliseconds >= timeLimit) return;
            }
        }

        private void GameLoop_UpdateTicking(object sender, UpdateTickingEventArgs e)
        {
            RespondToQueuedRequests(speechEngine.UpdateTickingRequestQueue);
            foreach (var btn in Input.Held.Values) {
                Input.SetDown(btn);
            }
            //this.speechEngine.SendEvent("UPDATE_TICKING");
        }

        private void GameLoop_UpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            eventHandler.CheckNewInGameEvent();
            RespondToQueuedRequests(speechEngine.UpdateTickedRequestQueue);
            foreach (var pair in ModEntry.Streams)
            {
                var id = pair.Key;
                var stream = pair.Value;
                if (stream.Name != "UPDATE_TICKED" || !e.IsMultipleOf((uint)stream.Data.ticks)) continue;
                string type = stream.Data.type;
                string error = null;
                dynamic value;
                try
                {
                    value = Requests.HandleRequestMessage(type);
                }
                catch (Exception exception)
                {
                    value = exception.ToString();
                    error = "STREAM_EXCEPTION";
                }
                var message = new { stream_id = id, value, error };
                this.speechEngine.SendMessage("STREAM_MESSAGE", message);
            }
            //this.speechEngine.SendEvent("UPDATE_TICKED");
        }
    }
}