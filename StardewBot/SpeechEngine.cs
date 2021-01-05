using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace StardewBot
{
    class SpeechEngine
    {
        Process Proc;
        public SpeechEngine() 
        {
            ModEntry.Log("engine");
            this.RunProcess();
            // Configure the process using the StartInfo properties.
            //this.Proc.StartInfo.FileName = "python";
            //this.Proc.StartInfo.Arguments = "C:\\Users\\evfre\\wp\\df\\df\\main.py";
            //this.Proc.StartInfo.WindowStyle = ProcessWindowStyle.Normal;
            //this.Proc.StartInfo.RedirectStandardError = true;
            //this.Proc.StandardError.
            //this.Proc.StartInfo; 
            //this.Proc.Start();
            //this.Proc.WaitForExit();// Waits here for the process to exit.
        }

        void RunProcess() {
            new Thread(() =>
            {
                Thread.CurrentThread.IsBackground = true;
                /* run your code here */
                ModEntry.Log("Hello, world");
                using (var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "C:\\Users\\evfre\\AppData\\Local\\Programs\\Python\\Python38\\python.exe",
                        Arguments = "C:\\Users\\evfre\\wp\\df\\df\\main.py",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true,
                    }
                })
                {
                    process.OutputDataReceived += (sender, args) => this.onMessage(args.Data);
                    process.ErrorDataReceived += (sender, args) => this.onError(args.Data);
                    //process.Exited += (sender, args) => this.onExit();

                    process.Start();
                    process.BeginOutputReadLine();
                    process.BeginErrorReadLine();

                    process.WaitForExit(); //you need this in order to flush the output buffer
                }
            }).Start();
        }

        void onExit() 
        {
            ModEntry.Log("Kaldi engine exited");
        }

        void onMessage(string message) {
            ModEntry.Log($"{message}");
        }

        void onError(string data) {
            ModEntry.Log($"Speech engine error: {data}");
        }
    }
}
