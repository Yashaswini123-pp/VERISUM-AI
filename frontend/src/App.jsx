import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Summarize from './pages/Summarize';
import Results from './pages/Results';
import History from './pages/History';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        <Navbar />
        <main className="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/summarize" element={<Summarize />} />
            <Route path="/results" element={<Results />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-200 bg-white">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
            <span>VeriSum AI — Evidence-Grounded Summarization &amp; Factual Verification</span>
            <span>Extractive TF-IDF + TextRank Pipeline</span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
