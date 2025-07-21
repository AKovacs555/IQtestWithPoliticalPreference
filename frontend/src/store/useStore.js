import create from 'zustand';

const useStore = create(set => ({
  user: null,
  quizProgress: 0,
  paymentStatus: null,
  setUser: user => set({ user }),
  setQuizProgress: quizProgress => set({ quizProgress }),
  setPaymentStatus: paymentStatus => set({ paymentStatus })
}));

export default useStore;
