using Newtonsoft.Json;
using StardewModdingAPI;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.IO.Pipes;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace StardewSpeak
{
    public class SpeechProcessNamedPipe
    {
        public string FileName;
        BinaryReader Reader;
        BinaryWriter Writer;
        NamedPipeServerStream Stream;
        NamedPipeServerStream WriterStream;
        public Action<string> OnMessage;
        public bool Connected = false;
        public BlockingCollection<string> SendQueue = new BlockingCollection<string>();
        public CancellationTokenSource WriteCancel = new CancellationTokenSource();
        public SpeechProcessNamedPipe(Action<string> onMessage)
        {
            this.OnMessage = onMessage;
            this.FileName = System.Guid.NewGuid().ToString();
            this.OpenStream();
            this.WriterStream = new NamedPipeServerStream(this.FileName + "Writer");
            this.Writer = new BinaryWriter(this.WriterStream);
            Task.Factory.StartNew(() => this.RunReader());
            Task.Factory.StartNew(() => this.RunWriter());

        }

        public void RunReader()
        {
            while (true)
            {
                this.Stream.WaitForConnection();
                while (true)
                {
                    try
                    {
                        string msg = this.ReadNext();
                        this.OnMessage(msg);
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
        public void RunWriter()
        {
            string next = null;
            while (true)
            {
                this.WriterStream.WaitForConnection();
                while (true)
                {
                    if (next == null)
                    {
                        try
                        {
                            next = this.SendQueue.Take(this.WriteCancel.Token);
                        }
                        catch (OperationCanceledException)
                        {
                            this.RestartWriter();
                            this.WriteCancel = new CancellationTokenSource();
                            break;
                        }
                    }
                    try
                    {
                        this.SendMessage(next);
                    }
                    catch (EndOfStreamException)
                    {
                        Console.WriteLine("Client disconnected.");
                        this.RestartWriter();
                        break;
                    }
                    next = null;
                }
            }
        }

        void OpenStream() 
        {
            // Open the named pipe.
            this.Stream = new NamedPipeServerStream(this.FileName + "Reader");
            this.Reader = new BinaryReader(this.Stream);
        }

        void RestartWriter()
        {
            if (this.WriterStream != null)
            {
                this.WriterStream.Close();
                this.WriterStream.Dispose();
            }
            this.WriterStream = new NamedPipeServerStream(this.FileName + "Writer");
            this.Writer = new BinaryWriter(this.WriterStream);
        }

        string ReadNext() 
        {
            var len = (int)this.Reader.ReadUInt32();            // Read string length
            var str = new string(this.Reader.ReadChars(len));    // Read string
            return str;
        }

        void SendMessage(string message) 
        {
            var buf = Encoding.UTF8.GetBytes(message);     // Get ASCII byte array     
            this.Writer.Write((uint)buf.Length);                // Write string length
            this.Writer.Write(buf);
        }

    }
}
