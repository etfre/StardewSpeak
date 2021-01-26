using Microsoft.Xna.Framework;
using StardewModdingAPI.Events;
using StardewValley;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{

    public class Stream
    {
        public string Name;
        public string Id;
        public dynamic Data;
        public Stream(string name, string id, dynamic streamData) 
        {
            this.Name = name;
            this.Id = id;
            this.Data = streamData;
        }

        public object Gather(UpdateTickedEventArgs e)
        {
            string state = this.Data.state;
            switch (state) 
            {
                case "PLAYER_STATUS":
                    return GameState.PlayerStatus();
                case "TOOL_STATUS":
                    return GameState.ToolStatus();
                case "CHARACTERS_AT_LOCATION":
                    return GameState.CharactersAtLocation(Game1.currentLocation);
            }
            return null;
        }

        public static List<dynamic> MessageStreams(Dictionary<string, Stream> streams, string streamName, dynamic messageValue) 
        {
            var messages = new List<dynamic>();
            foreach (var pair in streams)
            {
                var id = pair.Key;
                var stream = pair.Value;
                if (stream.Name == streamName)
                {
                    var message = new { stream_id = id, value = messageValue };
                    messages.Add(message);
                    //this.speechEngine.SendMessage("STREAM_MESSAGE", message);
                }
            }
            return messages;
        }

    }
}
