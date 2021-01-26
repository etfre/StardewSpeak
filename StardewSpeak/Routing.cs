using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Buildings;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace StardewSpeak
{

    public static class Routing
    {
        public static bool Ready = false;
        public static Dictionary<string, GameLocation> MapNamesToLocations = new Dictionary<string, GameLocation>();
        public static Dictionary<string, Building> MapNamesToBuildings = new Dictionary<string, Building>();
        private static Dictionary<string, HashSet<string>> MapConnections = new Dictionary<string, HashSet<string>>();

        public class LocationConnection {
            public int X;
            public int Y;
            public bool IsDoor;
            public LocationConnection(int x, int y, bool isDoor) {
                this.X = x;
                this.Y = y;
                this.IsDoor = isDoor;
            }
        }

        public static void Reset()
        {
            Ready = false;
            MapNamesToLocations.Clear();
            MapNamesToBuildings.Clear();
            if (Game1.IsMultiplayer && !Game1.IsMasterGame)
            {
                //client mode
                MapConnections.Clear();
                //Mod.instance.Monitor.Log("Starbot is now in multiplayer client mode.", LogLevel.Info);
                //Mod.instance.Monitor.Log("The server will need to have Starbot installed to proceed.", LogLevel.Info);
                //Mod.instance.Monitor.Log("Awaiting response from server...", LogLevel.Info);
                //Mod.instance.Helper.Multiplayer.SendMessage<int>(0, "authRequest");
            }
            else
            {
                //host/singleplayer mode
                MapConnections = BuildRouteCache();
                Ready = true;
            }
        }

        public static GameLocation FindLocationByName(string name)
        {
            foreach (var gl in Game1.locations) {
                if (gl.NameOrUniqueName == name) {
                    return gl;
                }
            }
            throw new InvalidOperationException($"Missing location {name}");
        }

        public static LocationConnection FindLocationConnection(GameLocation from, GameLocation to) {
            foreach (var warp in from.warps) 
            {
                if (warp.TargetName == to.NameOrUniqueName) {
                    return new LocationConnection(warp.X, warp.Y, false);
                }
            }
            foreach (var doorDict in from.doors)
            {
                foreach (var door in doorDict)
                {
                    var point = door.Key;
                    var loc = door.Value;
                    if (loc == to.NameOrUniqueName)
                    {
                        return new LocationConnection(point.X, point.Y, true);
                    }
                }
            }
                throw new InvalidOperationException($"Unable to find warp from {from.NameOrUniqueName} to {to.NameOrUniqueName}");
        }

        public static Dictionary<string, HashSet<string>> BuildRouteCache()
        {
            var returnValue = new Dictionary<string, HashSet<string>>();
            foreach (var gl in Game1.locations)
            {
                string key = gl.NameOrUniqueName;
                MapNamesToLocations.Add(key, gl);
                if (!string.IsNullOrWhiteSpace(key))// && !gl.isTemp())
                {
                    if (gl.warps != null && gl.warps.Count > 0)
                    {
                        returnValue[key] = new HashSet<string>();
                        foreach (var w in gl.warps) returnValue[key].Add(w.TargetName);
                        foreach (var d in gl.doors.Values) returnValue[key].Add(d);
                       // foreach (var s in MapConnections[key]) ModEntry.Log("It connects to " + s, LogLevel.Warn);
                    }
                }
                if (gl is StardewValley.Locations.BuildableGameLocation)
                {
                    StardewValley.Locations.BuildableGameLocation bl = gl as StardewValley.Locations.BuildableGameLocation;
                    foreach (var b in bl.buildings)
                    {
                        if (b.indoors.Value == null) continue;
                        if (!returnValue.ContainsKey(key)) returnValue[key] = new HashSet<string>();
                        returnValue[key].Add(b.indoors.Value.NameOrUniqueName);
                        //add the way in
                        returnValue[b.indoors.Value.NameOrUniqueName] = new HashSet<string>();
                        //add the way out
                        returnValue[b.indoors.Value.NameOrUniqueName].Add(key);
                        MapNamesToBuildings.Add(b.indoors.Value.NameOrUniqueName, b);
                    }
                }
            }
            return returnValue;
        }

        public static void Multiplayer_ModMessageReceived(object sender, ModMessageReceivedEventArgs e)
        {
            if (Game1.IsMasterGame && e.Type == "authRequest")
            {
                //Mod.instance.Monitor.Log("Starbot authorization requested by client. Approving...");
                //listen for authorization requests
                Dictionary<string, HashSet<string>> response = null;
                if (MapConnections.Count > 0)
                {
                    //host bot is active, use existing cache
                    response = MapConnections;
                }
                else
                {
                    response = BuildRouteCache();
                }
               // Mod.instance.Helper.Multiplayer.SendMessage<Dictionary<string, HashSet<string>>>(response, "authResponse");
            }
            else if (!Game1.IsMasterGame && e.Type == "authResponse")
            {
                //listen for authorization responses
                MapConnections = e.ReadAs<Dictionary<string, HashSet<string>>>();
               // Mod.instance.Monitor.Log("Starbot authorization request was approved by server.");
                //Mod.instance.Monitor.Log("Server offered routing data for " + MapConnections.Count + " locations.");
                Ready = true;
            }
            else if (e.Type == "taskAssigned")
            {
                string task = e.ReadAs<string>();
                //Mod.instance.Monitor.Log("Another player has taken task: " + task);
                Actions.ObjectivePool.RemoveAll(x => x.UniquePoolId == task);
            }
        }

        public static List<string> GetRoute(string destination)
        {
            if (!Ready) Reset();
            return GetRoute(Game1.player.currentLocation.NameOrUniqueName, destination);
        }

        public static List<string> GetRoute(string start, string destination)
        {
            if (!Ready) Reset();
            return SearchRoute(start, destination);
        }

        private static List<string> SearchRoute(string start, string target)
        {
            Func<dynamic, bool> validateTarget = (dynamic location) =>
            {
                if (location is Building)
                {
                    return location.indoors.Value.NameOrUniqueName == target;
                }
                return location.NameOrUniqueName == target;
            };
            return SearchRoute(start, validateTarget);
        }

        // bfs, just want to find shortest route
        private static List<string> SearchRoute(string start, Func<dynamic, bool> validateTarget) 
        {
            var queue = new Queue<string>();
            string target = null;
            queue.Enqueue(start);
            var seen = new HashSet<string> { start };
            var mapLocationToPrev = new Dictionary<string, string>();
            while (queue.Count > 0)
            {
                var currentLocationName = queue.Dequeue();
                dynamic currentLocation;
                if (MapNamesToLocations.ContainsKey(currentLocationName))
                {
                    currentLocation = MapNamesToLocations[currentLocationName];
                }
                else 
                {
                    currentLocation = MapNamesToBuildings[currentLocationName];
                }
                if (validateTarget(currentLocation)) 
                {
                    target = currentLocationName;
                    break;
                }
                foreach (var adj in MapConnections[currentLocationName])
                {
                    if (!seen.Contains(adj)) 
                    {
                        mapLocationToPrev[adj] = currentLocationName;
                        queue.Enqueue(adj);
                        seen.Add(adj);
                    }
                }
            }
            return target == null ? null : ReconstructRoute(target, mapLocationToPrev);
        }

        private static List<string> ReconstructRoute(string last, Dictionary<string, string> mapLocationToPrev) 
        {
            var route = new List<string> { last };
            var curr = last;
            while (mapLocationToPrev.ContainsKey(curr)) 
            {
                curr = mapLocationToPrev[curr];
                route.Add(curr);
            }
            route.Reverse();
            return route;
        }

        private static List<string> SearchRoute2(string step, string target, List<string> route = null, List<string> blacklist = null)
        {
            if (route == null) route = new List<string>();
            if (blacklist == null) blacklist = new List<string>();
            List<string> route2 = new List<string>(route);
            route2.Add(step);
            foreach (string s in MapConnections[step])
            {
                if (route.Contains(s) || blacklist.Contains(s)) continue;
                if (s == target)
                {
                    return route2;
                }
                List<string> result = SearchRoute2(s, target, route2, blacklist);
                if (result != null) return result;
            }
            blacklist.Add(step);
            return null;
        }
    }
}
