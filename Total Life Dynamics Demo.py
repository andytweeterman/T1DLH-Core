import React, { useState, useMemo } from 'react';
import { Activity, Brain, AlertTriangle, Utensils, Info, Moon, TrendingUp, Search, ShieldCheck } from 'lucide-react';

export default function App() {
  // --- STATE ---
  const [strain, setStrain] = useState(4.9);
  const [sleepQuality, setSleepQuality] = useState('Poor');
  const [foodQuery, setFoodQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [macroResult, setMacroResult] = useState(null);

  // --- CONE OF UNCERTAINTY CALCULATIONS ---
  const { coneUpper, coneLower, futureMid, conePoints, currentGlucose } = useMemo(() => {
    const currentG = 135;
    // Base divergence is 15 mg/dL. 
    // High strain adds up to 30 mg/dL. Poor sleep adds 20 mg/dL.
    const strainMultiplier = (strain / 21) * 30;
    const sleepMultiplier = sleepQuality === 'Poor' ? 20 : sleepQuality === 'Fair' ? 10 : 0;
    
    const maxDivergence = 15 + strainMultiplier + sleepMultiplier;
    
    // SVG Coordinates (Width: 300, Height: 150)
    // T=0 is at X=100. Y is inverted (0 is top).
    // Let's map 80 mg/dL to Y=130, 180 mg/dL to Y=20.
    const mapY = (val) => 150 - ((val - 60) * (150 / 140));
    
    const t0X = 100;
    const t0Y = mapY(currentG);
    
    const tEnd = 300;
    const futureG = 145; // slight upward drift
    const upperY = mapY(futureG + maxDivergence);
    const lowerY = mapY(futureG - maxDivergence);
    const midY = mapY(futureG);

    // Build the SVG path for the cone polygon
    const polygon = `${t0X},${t0Y} ${tEnd},${upperY} ${tEnd},${lowerY}`;
    
    return {
      currentGlucose: currentG,
      coneUpper: Math.round(futureG + maxDivergence),
      coneLower: Math.round(futureG - maxDivergence),
      futureMid: midY,
      conePoints: polygon
    };
  }, [strain, sleepQuality]);

  // --- MOCK USDA DATABASE LOOKUP ---
  const handleFoodSearch = () => {
    if (!foodQuery) return;
    setIsSearching(true);
    setMacroResult(null);

    // Simulate network delay and robust JSON parsing internally
    setTimeout(() => {
      const q = foodQuery.toLowerCase();
      let res = { carbs: 25, protein: 3, fat: 1, type: 'standard', name: foodQuery };
      
      if (q.includes('ipa') || q.includes('beer') || q.includes('alcohol')) {
        res = { carbs: 19, protein: 2, fat: 0, type: 'intoxicant', name: 'Hazy Double IPA', risk: 'Biphasic Hepatic Shutdown' };
      } else if (q.includes('pizza')) {
        res = { carbs: 35, protein: 12, fat: 14, type: 'complex', name: 'Pizza (1 Slice)', risk: 'Delayed Lipid-Protein Spike' };
      }

      setMacroResult(res);
      setIsSearching(false);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans p-4 sm:p-6 pb-20 select-none">
      {/* HEADER */}
      <div className="max-w-md mx-auto mb-6">
        <div className="flex justify-between items-center mb-1">
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-500" />
            Total Life Dynamics
          </h1>
          <div className="px-2 py-1 rounded bg-indigo-500/20 text-indigo-400 text-xs font-bold border border-indigo-500/30">
            BETA
          </div>
        </div>
        <p className="text-xs text-gray-400 font-medium tracking-wide uppercase">Enterprise Risk Engine</p>
      </div>

      <div className="max-w-md mx-auto space-y-4">

        {/* --- CONE OF UNCERTAINTY VISUALIZATION --- */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 shadow-xl">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-sm font-bold text-gray-300 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Live Predictive Cone
              </h2>
              <p className="text-xs text-gray-500 mt-1">Modeling T+3 Hours</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-black text-white">{currentGlucose}</div>
              <div className="text-xs text-emerald-400 font-bold">mg/dL ➔</div>
            </div>
          </div>

          {/* SVG Chart */}
          <div className="relative h-40 bg-gray-950 rounded-xl border border-gray-800/50 overflow-hidden">
            {/* Grid Lines */}
            <div className="absolute inset-0 flex flex-col justify-between p-2 opacity-20 pointer-events-none">
              <div className="border-b border-gray-600 h-1/3"></div>
              <div className="border-b border-gray-600 h-1/3"></div>
            </div>

            <svg viewBox="0 0 300 150" className="w-full h-full">
              {/* The Cone Polygon */}
              <polygon 
                points={conePoints} 
                fill="url(#coneGradient)" 
                opacity="0.4"
              />
              {/* Past Glucose Line */}
              <path 
                d="M 0,110 Q 25,120 50,115 T 100,74" 
                fill="none" 
                stroke="#10B981" 
                strokeWidth="3" 
                strokeLinecap="round"
              />
              {/* Current Point */}
              <circle cx="100" cy="74" r="4" fill="#10B981" />
              {/* Midline Prediction */}
              <line 
                x1="100" y1="74" x2="300" y2={futureMid} 
                stroke="#6366F1" strokeWidth="2" strokeDasharray="4 4" 
              />
              
              <defs>
                <linearGradient id="coneGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#6366F1" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#6366F1" stopOpacity="0.1" />
                </linearGradient>
              </defs>
            </svg>
            
            {/* Data Overlay */}
            <div className="absolute top-2 right-2 text-right">
              <div className="text-[10px] text-gray-400">Risk Surface</div>
              <div className="text-xs font-mono text-indigo-400">± {coneUpper - currentGlucose} mg/dL</div>
            </div>
          </div>

          {/* Real-time Modifiers */}
          <div className="mt-4 pt-4 border-t border-gray-800 space-y-4">
            <div>
              <div className="flex justify-between text-xs mb-2">
                <span className="text-gray-400 flex items-center gap-1"><Activity className="w-3 h-3"/> Whoop Strain: <span className="text-white font-bold ml-1">{strain.toFixed(1)}</span></span>
                <span className="text-gray-500 font-mono text-[10px]">Multiplier</span>
              </div>
              <input 
                type="range" min="0" max="21" step="0.1" value={strain} 
                onChange={(e) => setStrain(parseFloat(e.target.value))}
                className="w-full h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-xs flex items-center gap-1"><Moon className="w-3 h-3"/> Recovery State</span>
              <div className="flex gap-1">
                {['Good', 'Fair', 'Poor'].map(q => (
                  <button 
                    key={q}
                    onClick={() => setSleepQuality(q)}
                    className={`px-3 py-1 text-[10px] font-bold rounded-full border ${sleepQuality === q ? (q === 'Poor' ? 'bg-red-500/20 border-red-500/50 text-red-400' : q === 'Fair' ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400' : 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400') : 'bg-gray-800 border-gray-700 text-gray-500'}`}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* --- AGENTIC SYNTHESIS --- */}
        <div className="bg-indigo-950/30 border border-indigo-900/50 rounded-2xl p-4 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
          <h2 className="text-sm font-bold text-indigo-300 flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4" />
            Agentic Synthesis
          </h2>
          <div className="space-y-3">
            <p className="text-sm text-gray-300 leading-relaxed font-light">
              You're caught in a <strong className="text-white font-semibold">stress-glucose amplification loop</strong>: your 4.9 Whoop strain combined with the morning auto-shift to 'Stressed' signals that elevated cortisol is keeping your glucose elevated even when you're not eating.
            </p>
            <div className="bg-gray-950/50 rounded-lg p-3 border border-indigo-500/20">
              <p className="text-xs text-indigo-200 flex gap-2">
                <Info className="w-4 h-4 shrink-0 mt-0.5 text-indigo-400" />
                Until you interrupt the strain-sleep-glucose chain through a deliberate parasympathetic reset, your Time In Range will hover in this plateau.
              </p>
            </div>
          </div>
        </div>

        {/* --- USDA FOOD MACROS DATABASE --- */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 shadow-xl">
          <h2 className="text-sm font-bold text-gray-300 flex items-center gap-2 mb-3">
            <Utensils className="w-4 h-4" />
            Nutrition & Context
          </h2>
          
          <div className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input 
                type="text" 
                placeholder="Search USDA database..." 
                value={foodQuery}
                onChange={(e) => setFoodQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleFoodSearch()}
                className="w-full bg-gray-950 border border-gray-800 text-white text-sm rounded-lg pl-9 pr-3 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
            </div>
            <button 
              onClick={handleFoodSearch}
              disabled={isSearching || !foodQuery}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg text-sm font-bold transition-colors shadow-lg shadow-indigo-500/20 whitespace-nowrap"
            >
              {isSearching ? '...' : 'Look up Food Macros'}
            </button>
          </div>

          {macroResult && (
            <div className={`p-4 rounded-xl border animate-in fade-in slide-in-from-top-2 ${macroResult.type === 'intoxicant' ? 'bg-orange-950/20 border-orange-900/50' : 'bg-gray-950/50 border-gray-800'}`}>
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-bold text-white text-sm">{macroResult.name}</h3>
                {macroResult.type === 'intoxicant' && (
                  <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-orange-400 bg-orange-400/10 px-2 py-1 rounded">
                    <AlertTriangle className="w-3 h-3" /> Edge Case
                  </span>
                )}
              </div>

              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="bg-gray-900 rounded p-2 text-center border border-gray-800">
                  <div className="text-lg font-black text-white">{macroResult.carbs}g</div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wide">Carbs</div>
                </div>
                <div className="bg-gray-900 rounded p-2 text-center border border-gray-800">
                  <div className="text-lg font-black text-white">{macroResult.protein}g</div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wide">Protein</div>
                </div>
                <div className="bg-gray-900 rounded p-2 text-center border border-gray-800">
                  <div className="text-lg font-black text-white">{macroResult.fat}g</div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wide">Fat</div>
                </div>
              </div>

              {macroResult.risk && (
                <div className="flex items-start gap-2 text-xs p-2.5 bg-gray-900/50 rounded-lg border border-gray-800">
                  <ShieldCheck className={`w-4 h-4 shrink-0 mt-0.5 ${macroResult.type === 'intoxicant' ? 'text-orange-400' : 'text-indigo-400'}`} />
                  <p className="text-gray-300">
                    <span className="font-semibold text-white">ERM Override: </span> 
                    Detected {macroResult.risk}. Recommend delaying bolus to prevent delayed hepatic crash.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}