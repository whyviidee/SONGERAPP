import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { IoDownload, IoMusicalNotes, IoWifi, IoShield, IoBuild, IoChevronDown, IoWarning } from 'react-icons/io5'

const ICONS = {
  download: IoDownload,
  music: IoMusicalNotes,
  wifi: IoWifi,
  shield: IoShield,
  wrench: IoBuild,
}

const FAQ_SECTIONS = [
  {
    icon: 'download',
    title: 'Downloads & Formatos',
    items: [
      { q: 'Que formatos de áudio estão disponíveis?', a: 'SONGER suporta FLAC, MP3 320kbps, MP3 256kbps e MP3 128kbps. Podes mudar o formato em Settings. Para uso geral, MP3 320kbps é a escolha ideal — boa qualidade sem ficheiros enormes.' },
      { q: 'O FLAC do YouTube é lossless de verdade?', a: 'Não. O YouTube distribui áudio em formato AAC ou Opus (geralmente 128–256kbps). Quando escolhes FLAC com fonte YouTube, o SONGER descarrega esse áudio e converte-o para o container FLAC via FFmpeg. O ficheiro fica maior mas a qualidade é a do YouTube — não recupera informação que o YouTube já descartou. Para FLAC verdadeiro (lossless de CD), precisas do Soulseek.' },
      { q: 'Então MP3 320 e FLAC do YouTube soam igual?', a: 'Na prática, sim — o tecto de qualidade é o áudio do YouTube, não o formato do ficheiro. Para a maioria dos utilizadores é impossível distinguir. Se queres qualidade real, usa Soulseek para encontrar rips de CD verdadeiramente lossless.' },
      { q: 'Como funciona o modo Hybrid (Soulseek + YouTube)?', a: 'O SONGER tenta primeiro encontrar a música no Soulseek — que tem uma vasta biblioteca de FLAC e MP3 de alta qualidade partilhados por utilizadores reais. Se não encontrar (ou o Soulseek estiver offline), usa o YouTube como fallback automático. É o modo recomendado se tiveres Soulseek configurado.' },
      { q: 'Onde ficam guardados os ficheiros?', a: 'Na pasta que definiste em Settings → Download Path. Por defeito, os ficheiros são organizados por Artista/Álbum. Podes mudar a pasta em qualquer altura sem perder o que já foi descarregado.' },
      { q: 'Posso descarregar uma playlist inteira de uma vez?', a: 'Sim. Vai a Playlists → abre a playlist → "Download All". Todas as faixas são adicionadas à fila e descarregadas em sequência.' },
      { q: 'O download falhou. O que posso fazer?', a: 'Vai a Settings e verifica se tens um Download Path definido. Se estás a usar YouTube, verifica a ligação à internet. Se estás a usar Soulseek, confirma que o slskd está a correr. Podes tentar novamente na fila de downloads.' },
    ]
  },
  {
    icon: 'music',
    title: 'Spotify',
    items: [
      { q: 'Porque é que preciso de credenciais Spotify?', a: 'O SONGER usa a API oficial do Spotify para ler as tuas playlists, liked songs e metadados (nome, artista, álbum, capa). Não acede à tua conta para ouvir música — só lê informação.' },
      { q: 'A minha conta Spotify pode ser banida?', a: 'É extremamente improvável. O SONGER usa apenas a API oficial de leitura (sem streaming, sem controlo de reprodução). O Spotify não tem forma de saber que estás a descarregar música a partir dos metadados que lês.' },
      { q: 'Funciona com conta Spotify gratuita?', a: 'Sim. Todas as funcionalidades do SONGER — liked songs, playlists, pesquisa, metadados — funcionam com conta gratuita. O Premium não é necessário para nada no SONGER.' },
      { q: 'O SONGER acede à minha palavra-passe do Spotify?', a: 'Não. A autenticação usa OAuth 2.0 — o protocolo padrão da indústria. O SONGER nunca vê a tua palavra-passe. Autenticas directamente nos servidores do Spotify, que devolvem um token de acesso limitado (só leitura de biblioteca).' },
      { q: 'O que acontece quando o token do Spotify expira?', a: 'O SONGER renova o token automaticamente em background usando o refresh token. Não precisas de fazer login novamente. Só precisas de re-autenticar se fizeres logout manual ou apagares o ficheiro de token.' },
    ]
  },
  {
    icon: 'wifi',
    title: 'Soulseek',
    items: [
      { q: 'O que é o Soulseek?', a: 'Soulseek é uma rede P2P de partilha de música, activa desde 2000. É muito popular entre audiófilos por ter uma enorme biblioteca de FLAC lossless, vinis digitalizados e raridades impossíveis de encontrar noutros serviços. É o único caminho para FLAC verdadeiro no SONGER.' },
      { q: 'O Soulseek é obrigatório?', a: 'Não. O SONGER funciona perfeitamente com só o YouTube. O Soulseek é opcional e adiciona acesso a qualidade superior (FLAC real) e música difícil de encontrar no YouTube.' },
      { q: 'Porque é que aparece "Soulseek offline"?', a: 'O slskd não está a correr ou não está configurado. O SONGER liga ao slskd via API local (porta 5030 por defeito). Confirma que o slskd está iniciado. Se tens o hybrid activado, os downloads continuam via YouTube.' },
      { q: 'O meu IP fica exposto no Soulseek?', a: 'Tecnicamente sim — como em qualquer rede P2P, o teu IP é visível para outros utilizadores durante as transferências. Podes usar uma VPN para ocultar o IP se isso for uma preocupação. O Soulseek existe há mais de 20 anos com historial de acção legal mínima contra utilizadores individuais.' },
    ]
  },
  {
    icon: 'shield',
    title: 'Legal & Responsabilidade',
    items: [
      { q: 'É legal descarregar música com o SONGER?', a: 'Depende do país e do uso. Em muitos países, descarregar música protegida por direitos de autor para uso pessoal está numa zona cinzenta legal. O SONGER é uma ferramenta — a responsabilidade legal pelo uso é inteiramente do utilizador. Verifica as leis de direitos de autor do teu país antes de utilizar.' },
      { q: 'O SONGER guarda os meus dados?', a: 'Todos os dados ficam no teu computador. O SONGER não tem servidores externos, não envia telemetria, não regista o que descarregas. O ficheiro de configuração fica em ~/.songer/config.json — local, nunca partilhado.' },
      { q: 'O SONGER viola os Termos de Serviço do Spotify?', a: 'O uso da API do Spotify para leitura pessoal de playlists/biblioteca está dentro dos termos para aplicações em Development Mode. O SONGER não faz streaming não autorizado, não redistribui conteúdo Spotify, não usa a API para fins comerciais.' },
      { q: 'O que faço se receber um aviso legal?', a: 'Para de usar o SONGER imediatamente para o conteúdo em questão e procura aconselhamento jurídico. Os criadores do SONGER não fornecem assistência legal e não têm qualquer responsabilidade por acções legais resultantes do uso da ferramenta.' },
    ]
  },
  {
    icon: 'wrench',
    title: 'Problemas Comuns',
    items: [
      { q: 'O download fica a 0% e não avança.', a: 'Provável causa: sem ligação à internet, yt-dlp desactualizado, ou o YouTube bloqueou temporariamente o IP. Tenta novamente. Reiniciar o SONGER normalmente resolve.' },
      { q: 'Erro "ffmpeg not found" nos downloads.', a: 'O SONGER inclui o ffmpeg automaticamente via imageio-ffmpeg. Reiniciar o servidor normalmente resolve este problema.' },
      { q: 'As minhas playlists Spotify não aparecem.', a: 'O token Spotify pode ter expirado ou corrompido. Vai a Settings → Disconnect Spotify e volta a autenticar. O processo demora menos de um minuto.' },
      { q: 'A fila de downloads está vazia mas tenho músicas para descarregar.', a: 'Músicas com erro aparecem com ícone vermelho — podes tentar novamente ou removê-las. A fila não persiste entre sessões do SONGER.' },
      { q: 'Como actualizo o SONGER?', a: 'Descarrega a versão mais recente em songerapp.me e substitui a aplicação existente. As tuas definições e música descarregada não são afectadas.' },
    ]
  },
]

function FaqItem({ item }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 12, padding: '14px 0', background: 'none', border: 'none',
          color: '#f0f0f5', cursor: 'pointer', fontFamily: 'inherit', fontSize: 14,
          fontWeight: 500, textAlign: 'left',
        }}>
        <span>{item.q}</span>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }} style={{ flexShrink: 0 }}>
          <IoChevronDown size={16} style={{ color: 'rgba(240,240,245,0.4)' }} />
        </motion.div>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: 'hidden' }}>
            <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.55)', lineHeight: 1.7, margin: '0 0 16px', paddingRight: 24 }}>
              {item.a}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function FaqView() {
  return (
    <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f0f5', margin: 0 }}>Help & FAQ</h1>

      {/* Legal disclaimer */}
      <div style={{
        display: 'flex', gap: 14, padding: '16px 20px',
        background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
        borderRadius: 16,
      }}>
        <IoWarning size={18} style={{ color: '#f87171', flexShrink: 0, marginTop: 2 }} />
        <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.6)', lineHeight: 1.6, margin: 0 }}>
          <strong style={{ color: '#f87171' }}>Aviso Legal</strong> — O SONGER é uma ferramenta pessoal de código aberto.
          O utilizador é inteiramente responsável pelo uso que faz do software e pelo cumprimento
          das leis de direitos de autor do seu país. <strong style={{ color: 'rgba(240,240,245,0.8)' }}>Use de forma responsável.</strong>
        </p>
      </div>

      {/* Sections */}
      {FAQ_SECTIONS.map((section) => {
        const Icon = ICONS[section.icon] || IoMusicalNotes
        return (
          <div key={section.title} style={{
            background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.08)', borderRadius: 20, padding: '16px 24px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, paddingBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <Icon size={16} style={{ color: '#8b5cf6' }} />
              <span style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'rgba(240,240,245,0.5)' }}>
                {section.title}
              </span>
            </div>
            {section.items.map((item) => (
              <FaqItem key={item.q} item={item} />
            ))}
          </div>
        )
      })}
    </div>
  )
}
