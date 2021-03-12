using Newtonsoft.Json;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Newtonsoft.Json.Linq;
using StardewSpeak.Pathfinder;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Objects;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using StardewValley.Menus;
using System.Reflection;

namespace StardewSpeak
{
    public class SpeechEngine
    {
        Process Proc;
        private readonly object StandardInLock;
        public readonly object RequestQueueLock;
        public Queue<dynamic> RequestQueue;

        public SpeechEngine()
        {
            ModEntry.Log("engine");
            this.StandardInLock = new object();
            this.RequestQueueLock = new object();
            this.RequestQueue = new Queue<dynamic>();
        }

        public void LaunchProcess()
        {
            string rootDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            #if DEBUG
                ModEntry.Log("Running in debug mode");
                var fileName = "\"" + Path.Combine(rootDir, @"StardewSpeak\lib\speech-client\Scripts\python.exe") + "\"";
                var arguments = "\"" + Path.Combine(rootDir, @"StardewSpeak\lib\speech-client\speech-client\main.py") + "\"";
                Task.Factory.StartNew(() => RunProcessAsync(fileName, arguments));
            #else
                ModEntry.Log("Running in release mode");
                string exePath = "\"" + Path.Combine(rootDir, @"lib\speech-client\dist\speech-client.exe") + "\"";
                Task.Factory.StartNew(() => RunProcessAsync(exePath, null));
            #endif
        }

        public async Task<int> RunProcessAsync(string fileName, string args)
        {
            using (this.Proc = new Process
            {
                StartInfo =
                {
                    FileName = fileName,
                    Arguments = args,
                    UseShellExecute = false,
                    CreateNoWindow = true,

                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    RedirectStandardInput = true,
                },
                EnableRaisingEvents = true
            })
            {
                return await RunProcessAsync(this.Proc).ConfigureAwait(false);
            }
        }
        private Task<int> RunProcessAsync(Process process)
        {
            var tcs = new TaskCompletionSource<int>();

            process.Exited += (s, ea) => OnExit(process, tcs);
            process.OutputDataReceived += (s, ea) => this.OnMessage(ea.Data);
            process.ErrorDataReceived += (s, ea) => this.onError("ERR: " + ea.Data);

            bool started = process.Start();
            if (!started)
            {
                //you may allow for the process to be re-used (started = false) 
                //but I'm not sure about the guarantees of the Exited event in such a case
                throw new InvalidOperationException("Could not start process: " + process);
            }

            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            return tcs.Task;
        }
        void OnExit(Process process, TaskCompletionSource<int> tcs)
        {
            tcs.SetResult(process.ExitCode);
            ModEntry.Log("Kaldi engine exited. Restarting in 10 seconds...");
            System.Threading.Thread.Sleep(10000);
            LaunchProcess();
        }

        void OnMessage(string messageText)
        {
            dynamic msg;
            try
            {
                msg = JsonConvert.DeserializeObject(messageText);
            }
            catch
            {
                return;
            }
            lock (RequestQueueLock)
            {
                RequestQueue.Enqueue(msg);
            }
            //RespondToMessage(msg);
        }

        public void RespondToMessage(dynamic msg) 
        {
            dynamic resp;
            try
            {
                resp = HandleRequest(msg);
            }
            catch (Exception e)
            {
                string body = e.ToString();
                string error = "STACK_TRACE";
                resp = new { body, error };
            }
            string msgId = msg.id;
            this.SendResponse(msgId, resp.body, resp.error);
        }

        dynamic HandleRequest(dynamic msg) 
        {
            string msgType = msg.type;
            dynamic data = msg.data;
            string streamId;
            var player = Game1.player;
            int playerX = player.getTileX();
            int playerY = player.getTileY();
            dynamic body = null;
            dynamic error = null;
            switch (msgType)
            {
                case "LOG":
                    string toLog = data;
                    ModEntry.Log($"Speech engine message: {toLog}");
                    break;
                case "HEARTBEAT": // engine will shutdown if heartbeat not received after 10 seconds
                    break;
                case "PLAYER_POSITION":
                    body = GameState.PlayerPosition;
                    break;
                case "FACE_DIRECTION":
                    int direction = msg.data;
                    Game1.player.faceDirection(direction);
                    body = true;
                    break;
                case "NEW_STREAM":
                    {
                        streamId = data.stream_id;
                        string streamName = data.name;
                        object streamData = data.data;
                        var stream = new Stream(streamName, streamId, streamData);
                        // shallow copy as naive but simple way to avoid multithreading issues
                        var newStreams = new Dictionary<string, Stream>(ModEntry.Streams);
                        newStreams.Add(streamId, stream);
                        ModEntry.Streams = newStreams;
                        break;
                    }
                case "STOP_STREAM":
                    {
                        streamId = data;
                        // shallow copy as naive but simple way to avoid multithreading issues
                        var newStreams = new Dictionary<string, Stream>(ModEntry.Streams);
                        newStreams.Remove(streamId);
                        ModEntry.Streams = newStreams;
                        break;
                    }
                case "ROUTE":
                    {
                        GameLocation fromLocation = player.currentLocation;
                        string toLocationStr = data.toLocation;
                        GameLocation toLocation = Routing.FindLocationByName(toLocationStr);
                        body = Routing.GetRoute(fromLocation.NameOrUniqueName, toLocation.NameOrUniqueName);
                        break;
                    }
                case "ROUTE_INDOORS":
                    {
                        GameLocation fromLocation = player.currentLocation;
                        break;
                    }
                case "path_to_tile":
                    {
                        int targetX = data.x;
                        int targetY = data.y;
                        int cutoff = data.cutoff;
                        var path = Pathfinder.Pathfinder.FindPath(player.currentLocation, playerX, playerY, targetX, targetY, cutoff);
                        body = path;
                        break;
                    }
                case "PATH_TO_PLAYER":
                    {
                        int fromX = data.x;
                        int fromY = data.y;
                        int cutoff = data.cutoff;
                        var path = Pathfinder.Pathfinder.FindPath(player.currentLocation, fromX, fromY, playerX, playerY, cutoff);
                        body = path;
                        break;
                    }
                case "LOCATION_CONNECTION":
                    {
                        GameLocation fromLocation = player.currentLocation;
                        string toLocationStr = data.toLocation;
                        GameLocation toLocation = Routing.FindLocationByName(toLocationStr);
                        var locationConnection = Routing.FindLocationConnection(fromLocation, toLocation);
                        body = locationConnection;
                        break;
                    }
                case "GET_LOCATION_CONNECTIONS":
                    {
                        GameLocation fromLocation = player.currentLocation;
                        body = Routing.MapConnections[fromLocation.NameOrUniqueName];
                        break;
                    }
                case "PET_ANIMAL_BY_NAME":
                    {
                        string name = data.name;
                        FarmAnimal animal = Utils.FindAnimalByName(name);
                        bool didPet = false;
                        if (animal != null && !animal.wasPet)
                        {
                            animal.pet(player);
                            didPet = true;
                        }
                        body = didPet;
                        break;
                    }
                case "USE_TOOL_ON_ANIMAL_BY_NAME":
                    {
                        string name = data.name;
                        FarmAnimal animal = Utils.FindAnimalByName(name);
                        bool didUseTool = false;
                        if (animal != null && player.CurrentTool?.BaseName == animal.toolUsedForHarvest.Value)
                        {
                            Rectangle rect = animal.GetHarvestBoundingBox();
                            int x = rect.Center.X - Game1.viewport.X;
                            int y = rect.Center.Y - Game1.viewport.Y;
                            
                            Game1.setMousePosition(x, y);
                            Game1.pressUseToolButton();
                            //player.CurrentTool.beginUsing(player.currentLocation, (int)animal.Position.X, (int)animal.Position.Y, player);
                            didUseTool = true;
                        }
                        body = didUseTool;
                        break;
                    }
                case "GET_TREES":
                    {
                        body = GameState.Trees();
                        break;
                    }
                case "GET_DEBRIS":
                    {
                        body = GameState.Debris();
                        break;
                    }
                case "GET_HOE_DIRT":
                    {
                        body = GameState.HoeDirtTiles();
                        break;
                    }
                case "GET_LOCATION_OBJECTS":
                    {
                        body = GameState.LocationObjects();
                        break;
                    }
                case "GET_DIGGABLE_TILES":
                    {
                        List<dynamic> testTiles = data.tiles.ToObject<List<dynamic>>();
                        body = testTiles.Where(tile => Utils.IsTileHoeable(Game1.player.currentLocation, (int)tile.tileX, (int)tile.tileY));
                        break;
                    }
                case "EQUIP_ITEM":
                    {
                        string item = data.item;
                        body = Actions.EquipToolIfOnHotbar(item);
                        break;
                    }
                case "EQUIP_ITEM_INDEX":
                    {
                        int index = data.index;
                        Game1.player.CurrentToolIndex = index;
                        body = true;
                        break;
                    }
                case "GET_WATER_TILES":
                    {
                        bool[,] allTiles = Game1.player.currentLocation.waterTiles;
                        var wt = new List<List<int>>();
                        if (allTiles != null)
                        {
                            int width = allTiles.GetLength(0);
                            int height = allTiles.GetLength(1);
                            for (int x = 0; x < width; x++)
                            {
                                for (int y = 0; y < height; y++)
                                {
                                    bool isWaterTile = allTiles[x, y];
                                    if (isWaterTile)
                                    {
                                        var tile = new List<int> { x, y };
                                        wt.Add(tile);
                                    }
                                }
                            }
                        }
                        body = wt;
                        break;
                    }
                case "GET_ACTIVE_MENU":
                    body = Utils.SerializeMenu(Game1.activeClickableMenu);
                    break;
                case "GET_MOUSE_POSITION":
                    {
                        body = new List<int>{ Game1.getMouseX(), Game1.getMouseY()};
                        break;
                    }
                case "SET_MOUSE_POSITION":
                    {
                        int x = data.x;
                        int y = data.y;
                        bool fromViewport = data.from_viewport;
                        if (fromViewport)
                        {
                            x -= Game1.viewport.X;
                            y -= Game1.viewport.Y;
                        }
                        Game1.setMousePosition(x, y);
                        body = true;
                        break;
                    }
                case "SET_MOUSE_POSITION_ON_TILE":
                    {
                        int x = data.x*64 + 32 - Game1.viewport.X;
                        int y = data.y * 64 + 32 - Game1.viewport.Y;
                        Game1.setMousePosition(x, y);
                        body = true;
                        break;
                    }
                case "SET_MOUSE_POSITION_RELATIVE":
                    {
                        int x = data.x;
                        int y = data.y;
                        Game1.setMousePosition(Game1.getMouseX() + x, Game1.getMouseY() + y);
                        body = true;
                        break;
                    }
                case "MOUSE_CLICK":
                    {
                        var acm = Game1.activeClickableMenu;
                        if (acm == null)
                        {
                            body = false;
                        }
                        else
                        {
                            string btn = data.btn;
                            acm.receiveLeftClick(Game1.getMouseX(), Game1.getMouseY());
                            body = true;
                        }
                        body = true;
                        break;
                    }
                case "CLOSEST_SHIPPING_BIN":
                    {
                        break;
                    }
                case "CATCH_FISH":
                    {
                        var am = Game1.activeClickableMenu;
                        if (am is BobberBar)
                        {
                            var bb = am as BobberBar;
                            var distanceFromCatching = (float)Utils.GetPrivateField(bb, "distanceFromCatching");
                            bool treasure = (bool)Utils.GetPrivateField(bb, "treasure");
                            if (treasure)
                            {
                                Utils.SetPrivateField(bb, "treasureCaught", true);
                            }
                            Utils.SetPrivateField(bb, "distanceFromCatching", distanceFromCatching + 100);

                        }
                        break;
                    }
                case "GET_RESOURCE_CLUMPS":
                    {
                        body = GameState.ResourceClumps();
                        break;
                    }
            }
            return new { body, error };
        } 

        void onError(string data)
        {
            ModEntry.Log($"Speech engine error: {data}");
        }

        void SendResponse(string id, object value = null, object error = null) 
        {
            //var respData = new ResponseData(id, value);
            var respData = new { id, value, error };
            this.SendMessage("RESPONSE", respData);
        }

        public void SendMessage(string msgType, object data = null)     
        {
            var message = new MessageToEngine(msgType, data);
            var settings = new JsonSerializerSettings() { ReferenceLoopHandling = ReferenceLoopHandling.Ignore };
            settings.Error = (serializer, err) => err.ErrorContext.Handled = true;
            string msgStr = JsonConvert.SerializeObject(message, Formatting.None, settings);
            lock (this.StandardInLock) 
            {
                try
                {
                    this.Proc.StandardInput.WriteLine(msgStr);
                }
                catch (System.InvalidOperationException e) 
                {
                    
                }
            }
        }

        public void SendEvent(string eventType, object data = null) {
            var msg = new { eventType, data };
            this.SendMessage("ON_EVENT", msg);

        }
    }
    class MessageToEngine 
    {
        public string type;
        public object data;
        public MessageToEngine(string type, object data) 
        {
            this.type = type;
            this.data = data;
        }
    }
    class ResponseData
    {
        public string id;
        public object value;
        public ResponseData(string id, object value)
        {
            this.id = id;
            this.value = value;
        }
    }
}
