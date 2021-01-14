using Microsoft.Xna.Framework;
using StardewModdingAPI.Events;
using StardewValley;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewBot
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

            }
            return null;
        }

    }
}
