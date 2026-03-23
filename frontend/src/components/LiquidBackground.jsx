import { motion } from 'framer-motion'

export default function LiquidBackground() {
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 0, overflow: 'hidden', pointerEvents: 'none' }} aria-hidden>
      <motion.div
        style={{
          position: 'absolute',
          width: 500, height: 500,
          borderRadius: '50%',
          opacity: 0.12,
          background: 'radial-gradient(circle, #8b5cf6, transparent 70%)',
          filter: 'blur(80px)',
          top: '-10%', left: '-5%',
        }}
        animate={{
          x: [0, 120, -60, 80, 0],
          y: [0, 60, 120, -40, 0],
          scale: [1, 1.15, 0.9, 1.08, 1],
        }}
        transition={{ duration: 40, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        style={{
          position: 'absolute',
          width: 400, height: 400,
          borderRadius: '50%',
          opacity: 0.10,
          background: 'radial-gradient(circle, #06b6d4, transparent 70%)',
          filter: 'blur(80px)',
          bottom: '-10%', right: '-5%',
        }}
        animate={{
          x: [0, -80, 50, -30, 0],
          y: [0, -50, -100, 40, 0],
          scale: [1, 0.9, 1.1, 0.95, 1],
        }}
        transition={{ duration: 35, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        style={{
          position: 'absolute',
          width: 300, height: 300,
          borderRadius: '50%',
          opacity: 0.06,
          background: 'radial-gradient(circle, #a78bfa, transparent 70%)',
          filter: 'blur(60px)',
          top: '40%', left: '50%',
        }}
        animate={{
          x: [0, -40, 60, -20, 0],
          y: [0, 80, -30, 50, 0],
        }}
        transition={{ duration: 30, repeat: Infinity, ease: 'easeInOut' }}
      />
    </div>
  )
}
