using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
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
        public SpeechEngine()
        {
            ModEntry.Log("engine");
        }

        public void LaunchProcess()
        {
            ModEntry.Log("start wait");
            var fileName = "C:\\Users\\evfre\\AppData\\Local\\Programs\\Python\\Python38\\python.exe";
            var arguments = "C:\\Users\\evfre\\wp\\df\\df\\main.py";
            //var arguments = "C:\\Users\\evfre\\wp\\df\\df\\test.py";
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
            switch (msgType) 
            {
                case "LOG":
                    string toLog = msg.data;
                    ModEntry.Log($"Speech engine message: {toLog}");
                    break;
                case "HEARTBEAT": // engine will shutdown if heartbeat not received after 10 seconds
                    this.SendResponse(msgId);
                    break;
                case "PLAYER_POSITION":
                    this.SendResponse(msgId, GameState.PlayerPosition);
                    break;
                case "FACE_DIRECTION":
                    string direction = msg.data;
                    Game1.player.faceDirection(1);
                    break;
                case "NEW_STREAM":
                    streamId = data.stream_id;
                    string streamName = data.name;
                    uint ticks = data.ticks;
                    var stream = new Stream(streamName, streamId, ticks);
                    ModEntry.Streams.Add(streamId, stream);
                    break;
                case "STOP_STREAM":
                    streamId = data;
                    ModEntry.Streams.Remove(streamId);
                    break;

            }
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
            this.Proc.StandardInput.WriteLine(msgStr);
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
