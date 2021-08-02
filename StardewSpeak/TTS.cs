using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Speech.Synthesis;

namespace StardewSpeak
{
    public static class TTS
    {
        public static SpeechSynthesizer Synth = new SpeechSynthesizer();
        static TTS() 
        {
            Synth.SetOutputToDefaultAudioDevice(); 
        }

        public static void Speak(string text) 
        {
            Synth.SpeakAsyncCancelAll();
            Synth.SpeakAsync(text);
        }

    }
}
