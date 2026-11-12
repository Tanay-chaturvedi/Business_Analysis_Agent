import React, { useState } from 'react';
import { X, Lock, Mail, User, AlertCircle, ShieldCheck, ArrowRight } from 'lucide-react';
import { loginUser, registerUser } from '../../services/api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isRegister) {
        if (password.length < 8) {
          throw new Error('Password must be at least 8 characters long.');
        }
        const data = await registerUser(username, email, password);
        onAuthSuccess(data.user);
      } else {
        const data = await loginUser(username || email, password);
        onAuthSuccess(data.user);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#111111]/65 backdrop-blur-xs">
      <div className="relative w-full max-w-md editorial-panel rounded-xl shadow-2xl p-6 sm:p-8 overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-[#6B665E] hover:text-[#111111] dark:text-[#A69E92] dark:hover:text-white rounded-lg hover:bg-[#EAE3D5] dark:hover:bg-[#22201D] transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-11 h-11 rounded-lg bg-[#111111] text-white mb-3">
            <ShieldCheck className="w-5 h-5 text-[#D9541E]" />
          </div>
          <h3 className="font-heading text-xl font-bold text-[#111111] dark:text-[#F3EEE3]">
            {isRegister ? 'Create BizAdvisor Account' : 'Sign In to BizAdvisor'}
          </h3>
          <p className="text-xs text-[#6B665E] dark:text-[#A69E92] mt-1">
            {isRegister
              ? 'Register to save and manage your market evaluations securely.'
              : 'Access your saved restaurant feasibility analyses and scenarios.'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-[#A63222]/10 border border-[#A63222]/30 flex items-start gap-2.5 text-xs text-[#A63222] dark:text-[#E06C5B]">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#111111] dark:text-[#E6DED0] mb-1">
              {isRegister ? 'Username' : 'Username or Email'}
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B665E]" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={isRegister ? 'e.g. alex_chen' : 'Enter username or email'}
                className="w-full pl-10 pr-4 py-2.5 bg-[#F8F5EE] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg text-sm text-[#111111] dark:text-[#F3EEE3] placeholder:text-[#6B665E] focus:outline-none focus:border-[#D9541E] transition-colors"
              />
            </div>
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-semibold text-[#111111] dark:text-[#E6DED0] mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B665E]" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. alex@example.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-[#F8F5EE] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg text-sm text-[#111111] dark:text-[#F3EEE3] placeholder:text-[#6B665E] focus:outline-none focus:border-[#D9541E] transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#111111] dark:text-[#E6DED0] mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B665E]" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isRegister ? 'Min 8 characters with 1 number' : 'Enter your password'}
                className="w-full pl-10 pr-4 py-2.5 bg-[#F8F5EE] dark:bg-[#22201D] border border-[#C9BFAE] dark:border-[#3A352E] rounded-lg text-sm text-[#111111] dark:text-[#F3EEE3] placeholder:text-[#6B665E] focus:outline-none focus:border-[#D9541E] transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-2 py-2.5 px-4 editorial-btn-primary font-semibold text-sm rounded-lg flex items-center justify-center gap-2 cursor-pointer"
          >
            {isLoading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>{isRegister ? 'Register & Continue' : 'Sign In'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-[#6B665E] dark:text-[#A69E92]">
          {isRegister ? (
            <span>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsRegister(false);
                  setError(null);
                }}
                className="font-semibold text-[#D9541E] hover:underline cursor-pointer"
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsRegister(true);
                  setError(null);
                }}
                className="font-semibold text-[#D9541E] hover:underline cursor-pointer"
              >
                Create Account
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
