using Newtonsoft.Json;
using StardewModdingAPI;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.IO.Pipes;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{
    public class SpeechProcessNamedPipe
    {
        public string FileName;
        BinaryReader Reader;
        NamedPipeServerStream Stream;
        public Action<string> OnMessage;
        public bool Connected = false;
        public SpeechProcessNamedPipe(Action<string> onMessage)
        {
            this.OnMessage = onMessage;
            this.OpenStream();
            Task.Factory.StartNew(() => this.Run());
        }

        public void Run()
        {
            while (true)
            {
                this.Stream.WaitForConnection();
                while (true)
                {
                    Console.WriteLine("Connected.");
                    try
                    {
                        string msg = this.ReadNext();
                        this.OnMessage(msg);
                        Console.WriteLine("Read: \"{0}\"", msg);
                    }
                    catch (EndOfStreamException)
                    {
                        Console.WriteLine("Client disconnected.");
                        this.Stream.Close();
                        this.Stream.Dispose();
                        this.OpenStream();
                        break;
                    }
                }
            }
        }

        void OpenStream() 
        {
            this.FileName = System.Guid.NewGuid().ToString();
            this.FileName = "a";
            // Open the named pipe.
            this.Stream = new NamedPipeServerStream(this.FileName);
            this.Reader = new BinaryReader(this.Stream);
        }

        public string ReadNext() 
        {
            var len = (int)this.Reader.ReadUInt32();            // Read string length
            var str = new string(this.Reader.ReadChars(len));    // Read string
            return str;
        }

    }
}
