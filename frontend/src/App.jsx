import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar/Sidebar';
import Header from './components/Chat/Header';
import EmptyState from './components/Chat/EmptyState';
import AnalysisProgress from './components/Chat/AnalysisProgress';
import ChatMessage from './components/Chat/ChatMessage';
import ChatInput from './components/Chat/ChatInput';
import CompetitorModal from './components/Map/CompetitorModal';
import ScenarioModal from './components/Scenario/ScenarioModal';
import LocationPicker from './components/Location/LocationPicker';
import AuthModal from './components/Auth/AuthModal';
import {
  sendChatMessage,
  compareScenario,
  getHistory,
  getHistoryDetail,
  deleteHistoryItem,
  getAuthToken,
  getStoredUser,
  clearAuth,
  getCurrentUserProfile,
} from './services/api';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => getStoredUser());
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [historyItems, setHistoryItems] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [progressMode, setProgressMode] = useState('full');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Theme State with localStorage persistence & system preference fallback
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('biz_theme');
    if (saved) return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  // Sidebar Collapsed State with localStorage persistence
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    return localStorage.getItem('biz_sidebar_collapsed') === 'true';
  });

  // Modal States
  const [mapModal, setMapModal] = useState({ isOpen: false, competitors: [], locationName: '' });
  const [scenarioModal, setScenarioModal] = useState({ isOpen: false, currentParams: null, isLoading: false });
  const [isLocationPickerOpen, setIsLocationPickerOpen] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);

  const chatEndRef = useRef(null);

  // Sync theme class to document root element
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('biz_theme', theme);
  }, [theme]);

  // Persist sidebar collapsed state
  useEffect(() => {
    localStorage.setItem('biz_sidebar_collapsed', isSidebarCollapsed);
  }, [isSidebarCollapsed]);

  // Persist active session ID to localStorage
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('biz_active_session_id', currentSessionId);
    } else {
      localStorage.removeItem('biz_active_session_id');
    }
  }, [currentSessionId]);

  // Handle auth expired event from API client
  useEffect(() => {
    const handleAuthExpired = () => {
      setCurrentUser(null);
      setHistoryItems([]);
      handleNewAnalysis();
      setIsAuthModalOpen(true);
    };
    window.addEventListener('bizadvisor:auth_expired', handleAuthExpired);
    return () => window.removeEventListener('bizadvisor:auth_expired', handleAuthExpired);
  }, []);

  // Load history list on startup and restore active session if available
  useEffect(() => {
    const initStartup = async () => {
      if (getAuthToken()) {
        try {
          const profile = await getCurrentUserProfile();
          setCurrentUser(profile);
          await fetchHistoryList();
          const savedSessionId = localStorage.getItem('biz_active_session_id');
          if (savedSessionId) {
            handleSelectSession(savedSessionId);
          }
        } catch {
          setCurrentUser(null);
          setIsAuthModalOpen(true);
        }
      } else {
        setIsAuthModalOpen(true);
      }
    };
    initStartup();
  }, []);

  const handleAuthSuccess = async (user) => {
    setCurrentUser(user);
    handleNewAnalysis();
    await fetchHistoryList();
  };

  const handleLogout = () => {
    clearAuth();
    setCurrentUser(null);
    setHistoryItems([]);
    handleNewAnalysis();
    setIsAuthModalOpen(true);
  };

  // Scroll chat to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, progressStep, isLoading]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleToggleSidebarCollapse = () => {
    setIsSidebarCollapsed((prev) => !prev);
  };

  const fetchHistoryList = async () => {
    if (!getAuthToken()) {
      setHistoryItems([]);
      return;
    }
    try {
      const data = await getHistory();
      if (data && data.history) {
        setHistoryItems(data.history);
      }
    } catch (err) {
      console.warn('Could not load history list:', err);
    }
  };

  const handleSelectSession = async (sessionId) => {
    try {
      setIsLoading(true);
      setProgressMode('full');
      const detail = await getHistoryDetail(sessionId);
      if (detail && detail.messages) {
        setCurrentSessionId(sessionId);
        setMessages(detail.messages);
      } else {
        handleNewAnalysis();
      }
    } catch (err) {
      console.warn('Failed to load session history:', err);
      handleNewAnalysis();
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewAnalysis = () => {
    setCurrentSessionId(null);
    localStorage.removeItem('biz_active_session_id');
    setMessages([]);
    setErrorMessage(null);
    setProgressMode('full');
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteHistoryItem(sessionId);
      if (currentSessionId === sessionId) {
        handleNewAnalysis();
      }
      fetchHistoryList();
    } catch (err) {

      setErrorMessage('Failed to delete history item');
    }
  };

  // Main chat message submission
  const handleSendMessage = async (userInputText) => {
    if (!userInputText.trim() || isLoading) return;

    setErrorMessage(null);

    // Determine loading progress mode
    let mode = 'full';
    const lower = userInputText.toLowerCase();

    if (
      lower.startsWith('what is') ||
      lower.startsWith('what does') ||
      lower.startsWith('what are') ||
      lower.startsWith('why is') ||
      lower.startsWith('explain') ||
      lower.startsWith('how does') ||
      lower.startsWith('tell me') ||
      lower.includes('meaning of') ||
      lower.includes('what is shap') ||
      lower.includes('what does shap') ||
      lower.includes('what is google places') ||
      lower.includes('what is random forest')
    ) {
      mode = 'casual';
    } else if (
      (currentSessionId || messages.length > 0) &&
      (
        lower.includes('what if') ||
        lower.includes('reduce') ||
        lower.includes('increase') ||
        lower.includes('how about') ||
        lower.includes('switch') ||
        lower.includes('change')
      )
    ) {
      mode = 'scenario';
    }
    setProgressMode(mode);

    // 1. Append user message locally
    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: userInputText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setProgressStep(0);

    // Progress timers
    const progressTimer1 = setTimeout(() => setProgressStep(1), 800);
    const progressTimer2 = setTimeout(() => setProgressStep(2), 1800);
    const progressTimer3 = setTimeout(() => setProgressStep(3), 3200);
    const progressTimer4 = setTimeout(() => setProgressStep(4), 4500);

    try {
      // Call backend Chat Endpoint
      const response = await sendChatMessage(userInputText, currentSessionId);

      clearTimeout(progressTimer1);
      clearTimeout(progressTimer2);
      clearTimeout(progressTimer3);
      clearTimeout(progressTimer4);

      if (!currentSessionId && response.session_id) {
        setCurrentSessionId(response.session_id);
      }

      // Append assistant message with rich analysis cards depending on response mode
      const respMode = response.mode || (response.scenario_comparison || response.scenarioComparison ? 'scenario' : response.analysis ? 'full' : 'casual');

      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.ai_message,
        mode: respMode,
        analysis: respMode === 'full' ? response.analysis : null,
        scenarioComparison: respMode === 'scenario' ? (response.scenario_comparison || response.scenarioComparison) : null,
        parameters: response.parameters,
        timestamp: response.timestamp || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      fetchHistoryList();
    } catch (err) {
      clearTimeout(progressTimer1);
      clearTimeout(progressTimer2);
      clearTimeout(progressTimer3);
      clearTimeout(progressTimer4);

      setErrorMessage('Analysis couldn\'t be completed. ' + (err.message || 'Please check API key or input parameters.'));
    } finally {
      setIsLoading(false);
      setProgressStep(0);
    }
  };

  // Scenario modal submission
  const handleSubmitScenario = async (baselineParams, scenarioParams) => {
    try {
      setScenarioModal((prev) => ({ ...prev, isLoading: true }));
      setErrorMessage(null);

      // Call backend scenario comparison API with active sessionId
      const result = await compareScenario(baselineParams, scenarioParams, currentSessionId);

      setScenarioModal({ isOpen: false, currentParams: null, isLoading: false });
      fetchHistoryList();


      // Append scenario result message to conversation
      const scenarioMsg = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `**Scenario Comparison Executed:** Comparing original baseline against updated inputs for **${scenarioParams.location}**.`,
        scenarioComparison: result,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, scenarioMsg]);
    } catch (err) {
      setErrorMessage(err.message || 'Failed to compare scenario with backend');
    } finally {
      setScenarioModal((prev) => ({ ...prev, isLoading: false }));
    }
  };

  // Get current active parameters from latest assistant message
  const getLatestAssistantParams = () => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant' && messages[i].parameters) {
        return messages[i].parameters;
      }
    }
    return null;
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans transition-colors duration-200">
      {/* Left Sidebar */}
      <Sidebar
        historyItems={historyItems}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewAnalysis={handleNewAnalysis}
        onDeleteSession={handleDeleteSession}
        isOpen={isMobileSidebarOpen}
        onClose={() => setIsMobileSidebarOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={handleToggleSidebarCollapse}
        currentUser={currentUser}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Container */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
        {/* Header Bar */}
        <Header
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebarCollapse={handleToggleSidebarCollapse}
          onToggleMobileSidebar={() => setIsMobileSidebarOpen(true)}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          onNewAnalysis={handleNewAnalysis}
          currentTitle={
            messages.length > 0 && messages[0].content
              ? messages[0].content.slice(0, 32) + '...'
              : 'BizAdvisor'
          }
        />

        {/* Error Toast if any */}
        {errorMessage && (
          <div className="bg-rose-500/10 border-b border-rose-500/20 px-4 py-2.5 text-xs text-rose-700 dark:text-rose-300 flex items-center justify-between">
            <span>⚠️ {errorMessage}</span>
            <button onClick={() => setErrorMessage(null)} className="font-bold underline hover:opacity-80 cursor-pointer">
              Dismiss
            </button>
          </div>
        )}

        {/* Chat / Content Area */}
        <div className="flex-1 overflow-y-auto px-4 lg:px-8 py-6">
          {messages.length === 0 ? (
            <EmptyState onSelectPrompt={handleSendMessage} />
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onOpenMapModal={(competitors, compData) =>
                    setMapModal({
                      isOpen: true,
                      competitors: competitors || compData.competitors || [],
                      locationName: compData?.location || 'Target Area',
                    })
                  }
                  onCreateScenario={() =>
                    setScenarioModal({
                      isOpen: true,
                      currentParams: getLatestAssistantParams(),
                      isLoading: false,
                    })
                  }
                />
              ))}

              {/* Progress stepper when loading */}
              {isLoading && <AnalysisProgress currentStepIndex={progressStep} mode={progressMode} />}

              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {/* Bottom Chat Input Bar */}
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          hasMessages={messages.length > 0}
          onOpenLocationPicker={() => setIsLocationPickerOpen(true)}
          selectedLocation={selectedLocation}
        />
      </main>

      {/* Competitor Map Drawer Modal */}
      <CompetitorModal
        isOpen={mapModal.isOpen}
        onClose={() => setMapModal((prev) => ({ ...prev, isOpen: false }))}
        competitors={mapModal.competitors}
        locationName={mapModal.locationName}
      />

      {/* Scenario What-If Creator Modal */}
      <ScenarioModal
        isOpen={scenarioModal.isOpen}
        onClose={() => setScenarioModal((prev) => ({ ...prev, isOpen: false }))}
        currentParams={scenarioModal.currentParams}
        onSubmitScenario={handleSubmitScenario}
        isLoading={scenarioModal.isLoading}
      />

      {/* Historical Location Picker Modal */}
      <LocationPicker
        isOpen={isLocationPickerOpen}
        onClose={() => setIsLocationPickerOpen(false)}
        onSelectLocation={(loc) => setSelectedLocation(loc)}
      />

      {/* Authentication Modal (Login / Register) */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </div>
  );
}
