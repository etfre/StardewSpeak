using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using StardewBot.Pathfinder;
using StardewModdingAPI;
using StardewValley;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace StardewBot
{
    public class SpeechEngine
    {
        Process Proc;
        private readonly object StandardInLock;

        public SpeechEngine()
        {
            ModEntry.Log("engine");
            this.StandardInLock = new object();
        }

        public void LaunchProcess()
        {
            ModEntry.Log("start wait");
            var fileName = "\"" + Path.Combine(Environment.CurrentDirectory, @"Mods\StardewBot\StardewBot\lib\speech-client\Scripts\python.exe") + "\"";
            var arguments = "\"" + Path.Combine(Environment.CurrentDirectory, @"Mods\StardewBot\StardewBot\lib\speech-client\speech-client\main.py") + "\"";
            ModEntry.Log("end wait");
            Task.Factory.StartNew(() => RunProcessAsync(fileName, arguments));
            //await this.RunProcessAsync(fileName, arguments);
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
            process.OutputDataReceived += (s, ea) => this.onMessage(ea.Data);
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
            ModEntry.Log("Kaldi engine exited");
        }

        void onMessage(string messageText)
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
            string msgType = msg.type;
            string msgId = msg.id;
            dynamic data = msg.data;
            string streamId;
            var player = Game1.player;
            int playerX = player.getTileX();
            int playerY = player.getTileY();
            dynamic resp = null;
            switch (msgType)
            {
                case "LOG":
                    string toLog = data;
                    ModEntry.Log($"Speech engine message: {toLog}");
                    break;
                case "HEARTBEAT": // engine will shutdown if heartbeat not received after 10 seconds
                    break;
                case "PLAYER_POSITION":
                    resp = GameState.PlayerPosition;
                    break;
                case "FACE_DIRECTION":
                    int direction = msg.data;
                    Game1.player.faceDirection(direction);
                    resp = true;
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
                        resp = new List<string>();
                        if (fromLocation.NameOrUniqueName == toLocation.NameOrUniqueName)
                        {
                            resp.Add(toLocation.NameOrUniqueName);
                        }
                        else {
                            resp = Routing.GetRoute(fromLocation.NameOrUniqueName, toLocation.NameOrUniqueName);
                        }
                        break;
                    }
                case "PATH_TO_POSITION":
                    {
                        int targetX = data.x;
                        int targetY = data.y;
                        var path = Pathfinder.Pathfinder.FindPath(player.currentLocation, playerX, playerY, targetX, targetY);
                        resp = path;
                        break;
                    }
                case "PATH_TO_WARP":
                    {
                        GameLocation fromLocation = player.currentLocation;
                        string toLocationStr = data.toLocation;
                        GameLocation toLocation = Routing.FindLocationByName(toLocationStr);
                        var warp = Routing.FindWarp(fromLocation, toLocation);
                        var path = Pathfinder.Pathfinder.FindPath(fromLocation, playerX, playerY, warp.X, warp.Y);
                        resp = path;
                        break;
                    }
                case "GET_TREES": 
                    {
                        resp = GameState.Trees();
                        break;
                    }
                case "GET_DEBRIS":
                    {
                        resp = GameState.Debris();
                        break;
                    }
                case "GET_HOE_DIRT":
                    {
                        resp = GameState.HoeDirtTiles();
                        break;
                    }
                case "EQUIP_ITEM":
                    {
                        string item = data.item;
                        resp = Actions.EquipToolIfOnHotbar(item);
                        break;
                    }

            }
            this.SendResponse(msgId, resp);
        }

        void onError(string data)
        {
            ModEntry.Log($"Speech engine error: {data}");
        }

        void SendResponse(string id, object value = null) 
        {
            var respData = new ResponseData(id, value);
            this.SendMessage("RESPONSE", respData);
        }
        public void SendMessage(string msgType, object data = null)     
        {
            var message = new MessageToEngine(msgType, data);
            string msgStr = JsonConvert.SerializeObject(message);
            lock (this.StandardInLock) 
            {
                this.Proc.StandardInput.WriteLine(msgStr);
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
