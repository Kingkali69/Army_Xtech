#!/usr/bin/env python3
# WINDOWS PEER - Unified GhostHUD peer using unified engine

import sys
import os

# Import unified engine and adapter
from ghostops_adapter import GhostOpsAdapter

# Embedded HTML (full feature set)
HTML = """<!DOCTYPE html>
<html>
<head>
  <title>GhostHUD</title>
  <style>
    body{background:#111;color:#0f0;font-family:monospace;margin:0;padding:0}
    .container{max-width:1200px;margin:0 auto;padding:20px}
    .header{text-align:center;border-bottom:1px solid #0f0;padding:20px 0;position:relative}
    .ghost-logo{width:140px;height:180px;margin:0 auto 20px;position:relative;filter:drop-shadow(0 0 25px #0f0)}
    .ghost-logo svg{width:100%;height:100%}
    .logo{font-size:48px;letter-spacing:5px;text-shadow:0 0 10px #0f0;margin-top:10px}
    .logo-online{color:#0f0;font-size:14px;margin-top:5px;text-shadow:0 0 5px #0f0}
    .controls{display:flex;justify-content:space-between;flex-wrap:wrap;margin:20px 0}
    .btn{background:#000;color:#0f0;border:1px solid #0f0;padding:10px 15px;margin:5px;cursor:pointer;font-family:monospace;transition:all .3s;box-shadow:0 0 5px #0f0}
    .btn:hover{background:#030;box-shadow:0 0 15px #0f0}
    .btn.red{border-color:#f33;color:#f33;box-shadow:0 0 5px #f33}
    .btn.red:hover{background:#300;box-shadow:0 0 15px #f33}
    .btn.blue{border-color:#33f;color:#33f;box-shadow:0 0 5px #33f}
    .btn.blue:hover{background:#003;box-shadow:0 0 15px #33f}
    .btn.purple{border-color:#93f;color:#93f;box-shadow:0 0 5px #93f}
    .btn.purple:hover{background:#303;box-shadow:0 0 15px #93f}
    .btn.active{background:#030}
    .btn.active-tunnel{background:#030;box-shadow:0 0 20px #0f0}
    .btn.master-control{background:#030;border-color:#0f0;color:#0f0;box-shadow:0 0 25px #0f0;animation:glow-green 2s ease-in-out infinite}
    .btn.peer-control{background:#000;border-color:#666;color:#666;box-shadow:0 0 5px #666;cursor:not-allowed}
    .btn.idle-control{border-color:#0f0;color:#0f0;box-shadow:0 0 5px #0f0}
    @keyframes glow-green{0%,100%{box-shadow:0 0 25px #0f0}50%{box-shadow:0 0 40px #0f0}}
    .status-item.tunnel-active{box-shadow:0 0 10px #0f0;background:rgba(0,40,0,.4)}
    .status-item.connected{box-shadow:0 0 10px #0f0;background:rgba(0,40,0,.4)}
    .status-item.standalone{box-shadow:0 0 10px #ff0;background:rgba(40,40,0,.4)}
    .status-item.connecting{box-shadow:0 0 10px #33f;background:rgba(0,0,40,.4)}
    .status-item.home-lan{box-shadow:0 0 10px #0f0;background:rgba(0,40,0,.4)}
    .status-item.away{box-shadow:0 0 10px #f90;background:rgba(40,20,0,.4)}
    .panel{border:1px solid #0f0;margin-bottom:20px;background:rgba(0,20,0,.3);box-shadow:0 0 10px #0f0}
    .panel-header{border-bottom:1px solid #0f0;padding:10px;background:rgba(0,20,0,.5)}
    .panel-body{padding:15px}
    .status-info{display:flex;justify-content:space-between;margin-bottom:20px;flex-wrap:wrap}
    .status-item{padding:10px;border:1px solid #0f0;flex:1;margin:5px;text-align:center;background:rgba(0,20,0,.2)}
    .progress-bar{height:20px;width:100%;background:#000;margin-top:5px;border:1px solid #0f0}
    .progress{height:100%;background:#0f0;width:0;transition:width .3s}
    pre{background:#000;padding:10px;border:1px solid #0f0;overflow:auto;max-height:200px}
    .network-map{height:300px;border:1px solid #0f0;background:#000;position:relative;margin-top:10px}
    .node{position:absolute;width:40px;height:40px;border-radius:50%;background:#0f0;display:flex;align-items:center;justify-content:center;font-weight:bold;box-shadow:0 0 10px #0f0}
    .connection{position:absolute;height:2px;background:#0f0;transform-origin:left center;box-shadow:0 0 5px #0f0}
    .notification{position:fixed;top:20px;right:20px;padding:15px;background:rgba(0,20,0,.8);border:1px solid #0f0;box-shadow:0 0 15px #0f0;z-index:1000;transition:all .5s;opacity:0}
    .show{opacity:1}
    .tools{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:15px;margin-top:20px}
    .tool{border:1px solid #0f0;padding:15px;cursor:pointer;transition:all .3s;background:rgba(0,20,0,.2)}
    .tool:hover{background:rgba(0,40,0,.4);box-shadow:0 0 15px #0f0}
    .tool h3{margin-top:0}
    .tool-output-modal{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:90%;max-width:900px;height:80vh;background:#000;border:2px solid #0f0;padding:0;z-index:10001;box-shadow:0 0 30px #0f0;flex-direction:column}
    .tool-output-modal.active{display:flex}
    .tool-modal-header{background:rgba(0,20,0,.5);padding:15px;border-bottom:1px solid #0f0;display:flex;justify-content:space-between;align-items:center}
    .tool-modal-title{color:#0f0;font-size:20px;font-weight:bold;text-shadow:0 0 10px #0f0}
    .tool-modal-close{background:#f33;color:#fff;border:none;padding:5px 15px;cursor:pointer;font-family:monospace}
    .tool-modal-tabs{display:flex;background:rgba(0,10,0,.5);border-bottom:1px solid #0f0}
    .tool-modal-tab{flex:1;padding:10px;background:rgba(0,20,0,.3);border:none;border-right:1px solid #0f0;color:#0f0;cursor:pointer;font-family:monospace;transition:all .3s}
    .tool-modal-tab.active{background:rgba(0,40,0,.6);box-shadow:0 0 10px #0f0}
    .tool-modal-tab:hover{background:rgba(0,30,0,.5)}
    .tool-modal-content{flex:1;overflow:auto;padding:20px;background:#000}
    .tool-modal-panel{display:none}
    .tool-modal-panel.active{display:block}
    .tool-code-selector{display:flex;gap:10px;margin-bottom:15px;align-items:center}
    .tool-code-selector label{color:#0f0}
    .tool-code-selector select{background:#000;color:#0f0;border:1px solid #0f0;padding:5px 10px;font-family:monospace}
    .tool-code-output{background:#000;border:1px solid #0f0;padding:15px;color:#0f0;font-family:monospace;white-space:pre-wrap;overflow:auto;max-height:500px;min-height:200px}
    .tool-result-output{background:#000;border:1px solid #0f0;padding:15px;color:#0f0;font-family:monospace;white-space:pre-wrap;overflow:auto;max-height:500px;min-height:200px}
    .code-viewer-modal{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:1000px;height:800px;background:#000;border:3px solid #0f0;z-index:10002;box-shadow:0 0 40px #0f0;flex-direction:column}
    .code-viewer-modal.active{display:flex}
    .code-viewer-header{background:rgba(0,30,0,.8);padding:15px 20px;border-bottom:2px solid #0f0;display:flex;justify-content:space-between;align-items:center}
    .code-viewer-title{color:#0f0;font-size:20px;font-weight:bold;text-shadow:0 0 10px #0f0;text-transform:uppercase}
    .code-viewer-close{background:#f33;color:#fff;border:none;padding:8px 20px;cursor:pointer;font-family:monospace;font-weight:bold;box-shadow:0 0 10px #f33;transition:all .3s}
    .code-viewer-close:hover{background:#f55;box-shadow:0 0 20px #f33}
    .code-viewer-tabs{display:flex;background:rgba(0,20,0,.5);border-bottom:2px solid #0f0}
    .code-viewer-tab{flex:1;padding:12px;background:rgba(0,20,0,.3);border:none;border-right:1px solid #0f0;color:#0f0;cursor:pointer;font-family:monospace;font-size:14px;font-weight:bold;transition:all .3s}
    .code-viewer-tab:last-child{border-right:none}
    .code-viewer-tab.active{background:rgba(0,60,0,.7);box-shadow:inset 0 0 15px #0f0;color:#0ff}
    .code-viewer-tab:hover:not(.active){background:rgba(0,40,0,.5)}
    .code-viewer-content{flex:1;overflow:auto;padding:0;background:#000;position:relative}
    .code-viewer-panel{display:none;height:100%;padding:20px;overflow:auto}
    .code-viewer-panel.active{display:block}
    .code-viewer-code{background:#000;border:1px solid #0f0;padding:15px;color:#0f0;font-family:monospace;white-space:pre;overflow:auto;font-size:13px;line-height:1.5;min-height:400px}
    .code-viewer-actions{padding:15px 20px;border-top:2px solid #0f0;background:rgba(0,20,0,.5);display:flex;gap:10px;justify-content:flex-end}
    .code-viewer-btn{background:#000;color:#0f0;border:2px solid #0f0;padding:10px 20px;cursor:pointer;font-family:monospace;font-weight:bold;transition:all .3s;box-shadow:0 0 10px #0f0}
    .code-viewer-btn:hover{background:#030;box-shadow:0 0 20px #0f0}
    .code-viewer-btn.run{border-color:#33f;color:#33f;box-shadow:0 0 10px #33f}
    .code-viewer-btn.run:hover{background:#003;box-shadow:0 0 20px #33f}
    .code-warning{background:rgba(255,100,0,.2);border:1px solid #f80;padding:10px;margin-bottom:15px;color:#f80;font-size:12px}
    .syntax-comment{color:#888}
    .syntax-string{color:#0ff}
    .syntax-keyword{color:#f0f}
    .syntax-function{color:#ff0}
    @media(max-width:768px){.logo{font-size:32px}.controls{flex-direction:column}.status-info{flex-direction:column}.tool-output-modal{width:95%;height:90vh}.code-viewer-modal{width:95%;height:90vh}}
    
    /* GHOST AGENT - Floating AI Assistant */
    .ghost-float{position:fixed;bottom:30px;right:30px;z-index:99999;display:flex;flex-direction:column;align-items:flex-end;gap:10px}
    .ghost-avatar{width:80px;height:80px;border-radius:50%;cursor:pointer;transition:all .3s;border:3px solid #0f0;box-shadow:0 0 25px rgba(0,255,65,.5);animation:ghost-hover 3s ease-in-out infinite;background:linear-gradient(135deg,#0a1a0a 0%,#0d2818 100%);overflow:hidden}
    .ghost-avatar img{width:100%;height:100%;object-fit:cover}
    .ghost-avatar:hover{transform:scale(1.1);box-shadow:0 0 40px rgba(0,255,65,.8)}
    .ghost-avatar.listening{border-color:#0ff;box-shadow:0 0 40px rgba(0,255,255,.8);animation:ghost-listen .5s ease-in-out infinite}
    .ghost-avatar.speaking{border-color:#f0f;box-shadow:0 0 40px rgba(255,0,255,.8);animation:ghost-speak .3s ease-in-out infinite}
    @keyframes ghost-hover{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
    @keyframes ghost-listen{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
    @keyframes ghost-speak{0%,100%{transform:scale(1)}50%{transform:scale(1.03)}}
    .ghost-panel{position:fixed;bottom:130px;right:30px;width:380px;max-height:500px;background:#0a0a0a;border:2px solid #0f0;border-radius:15px;display:none;flex-direction:column;z-index:99998;box-shadow:0 0 30px rgba(0,255,65,.3)}
    .ghost-panel.show{display:flex}
    .ghost-panel-header{padding:15px;border-bottom:1px solid #1a3a1a;display:flex;justify-content:space-between;align-items:center;background:rgba(0,30,0,.5);border-radius:13px 13px 0 0}
    .ghost-panel-title{color:#0f0;font-weight:bold;font-size:16px;text-shadow:0 0 10px #0f0}
    .ghost-panel-close{background:none;border:none;color:#f33;font-size:24px;cursor:pointer}
    .ghost-tts-btn{background:none;border:none;color:#0f0;font-size:18px;cursor:pointer;padding:5px;transition:all .2s}
    .ghost-tts-btn:hover{transform:scale(1.2);color:#0ff}
    .ghost-tts-btn.muted{opacity:.5;color:#666}
    .ghost-messages{flex:1;overflow-y:auto;padding:15px;max-height:280px;display:flex;flex-direction:column;gap:10px}
    .ghost-msg{padding:10px 14px;border-radius:12px;max-width:85%;animation:msg-in .3s ease-out}
    @keyframes msg-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
    .ghost-msg.user{align-self:flex-end;background:linear-gradient(135deg,#1a3a1a,#0d2818);border:1px solid #0f0;color:#0f0}
    .ghost-msg.ghost{align-self:flex-start;background:#161b22;border:1px solid #2a2a4a;color:#e0e0e0}
    .ghost-input-area{display:flex;gap:8px;padding:12px;border-top:1px solid #1a3a1a;background:rgba(0,10,0,.5);border-radius:0 0 13px 13px}
    .ghost-input{flex:1;background:#0d1117;border:1px solid #1a3a1a;border-radius:20px;padding:10px 15px;color:#0f0;font-family:monospace;outline:none}
    .ghost-input:focus{border-color:#0f0;box-shadow:0 0 10px rgba(0,255,65,.3)}
    .ghost-btn{width:40px;height:40px;border-radius:50%;border:1px solid #1a3a1a;background:#0d1117;color:#0f0;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}
    .ghost-btn:hover{border-color:#0f0;box-shadow:0 0 15px rgba(0,255,65,.5)}
    .ghost-btn.recording{border-color:#f33;background:rgba(255,0,64,.2);animation:rec-pulse 1s infinite}
    @keyframes rec-pulse{0%,100%{box-shadow:0 0 15px rgba(255,0,64,.5)}50%{box-shadow:0 0 30px rgba(255,0,64,.8)}}
    .ghost-typing{display:none;padding:10px;align-self:flex-start}
    .ghost-typing.show{display:flex;gap:4px}
    .ghost-dot{width:8px;height:8px;background:#0ff;border-radius:50%;animation:dot-bounce 1.4s infinite ease-in-out}
    .ghost-dot:nth-child(2){animation-delay:.2s}
    .ghost-dot:nth-child(3){animation-delay:.4s}
    @keyframes dot-bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-8px)}}
    .ghost-status{width:12px;height:12px;border-radius:50%;background:#0f0;position:absolute;bottom:5px;right:5px;box-shadow:0 0 10px #0f0;animation:status-pulse 2s infinite}
    @keyframes status-pulse{0%,100%{opacity:1}50%{opacity:.5}}
    
    /* ═══════════════════════════════════════════════════════════════
       GHOSTVERSE CONTROL ROOM - Immersive Battle Interface
       ═══════════════════════════════════════════════════════════════ */
    .control-room{position:fixed;top:0;left:0;width:100%;height:100vh;background:radial-gradient(ellipse at center,#000 0%,#0a0a0a 100%);overflow:hidden;z-index:1}
    .neon-frame{position:absolute;top:50px;left:50%;transform:translateX(-50%);width:95%;height:calc(100vh - 250px);border:4px solid #ff00ff;box-shadow:0 0 40px #ff00ff,inset 0 0 40px rgba(255,0,255,.3);border-radius:10px;background:rgba(0,0,0,.8);padding:20px}
    .neon-frame::before{content:'';position:absolute;top:-4px;left:-4px;right:-4px;bottom:-4px;border:2px solid #bf00ff;border-radius:10px;box-shadow:0 0 20px #bf00ff;animation:neon-pulse 2s ease-in-out infinite}
    @keyframes neon-pulse{0%,100%{opacity:1;box-shadow:0 0 20px #bf00ff}50%{opacity:.7;box-shadow:0 0 40px #bf00ff}}
    .screen-wall{display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(2,1fr);gap:15px;height:100%;width:100%}
    .control-screen{background:linear-gradient(135deg,#0a0a0a 0%,#1a0a1a 100%);border:2px solid #00ffff;border-radius:8px;padding:15px;position:relative;overflow:hidden;box-shadow:0 0 20px rgba(0,255,255,.3),inset 0 0 30px rgba(0,255,255,.1)}
    .control-screen::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#00ffff,transparent);animation:scan-line 3s linear infinite}
    @keyframes scan-line{0%{top:0}100%{top:100%}}
    .screen-header{color:#00ffff;font-size:14px;font-weight:bold;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;text-shadow:0 0 10px #00ffff;border-bottom:1px solid rgba(0,255,255,.3);padding-bottom:5px}
    .screen-content{height:calc(100% - 40px);overflow:hidden;position:relative}
    
    /* Screen 1 - Opponent Avatar */
    .opponent-avatar{display:flex;align-items:center;justify-content:center;height:100%;position:relative}
    .avatar-placeholder{width:120px;height:120px;border-radius:50%;border:3px solid #ff00ff;box-shadow:0 0 30px #ff00ff;background:radial-gradient(circle,#1a0a1a 0%,#000 100%);display:flex;align-items:center;justify-content:center;font-size:48px;animation:avatar-pulse 2s ease-in-out infinite}
    @keyframes avatar-pulse{0%,100%{transform:scale(1);box-shadow:0 0 30px #ff00ff}50%{transform:scale(1.05);box-shadow:0 0 50px #ff00ff}}
    .avatar-status{position:absolute;bottom:10px;left:50%;transform:translateX(-50%);color:#00ffff;font-size:11px;text-align:center}
    
    /* Screen 2 - Network Map */
    .network-visualization{width:100%;height:100%;position:relative}
    .network-node{position:absolute;width:20px;height:20px;border-radius:50%;background:#00ffff;box-shadow:0 0 15px #00ffff;animation:node-pulse 2s ease-in-out infinite}
    @keyframes node-pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.7;transform:scale(1.2)}}
    .network-connection{position:absolute;height:2px;background:linear-gradient(90deg,transparent,#00ffff,transparent);transform-origin:left center;opacity:.6}
    
    /* Screen 3 - Technique Radar */
    .radar-container{width:100%;height:100%;position:relative;display:flex;align-items:center;justify-content:center}
    .radar-circle{position:absolute;border:2px solid #00ffff;border-radius:50%;box-shadow:0 0 20px rgba(0,255,255,.5)}
    .radar-circle:nth-child(1){width:60%;height:60%;top:20%;left:20%}
    .radar-circle:nth-child(2){width:80%;height:80%;top:10%;left:10%}
    .radar-circle:nth-child(3){width:100%;height:100%}
    .radar-center{position:absolute;width:10px;height:10px;background:#00ffff;border-radius:50%;box-shadow:0 0 20px #00ffff;top:50%;left:50%;transform:translate(-50%,-50%)}
    .radar-blip{position:absolute;width:8px;height:8px;background:#ff00ff;border-radius:50%;box-shadow:0 0 15px #ff00ff;animation:blip-pulse 1.5s ease-in-out infinite}
    @keyframes blip-pulse{0%,100%{opacity:1}50%{opacity:.5}}
    
    /* Screen 4 - Scoreboard */
    .scoreboard{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%}
    .score-display{font-size:48px;font-weight:bold;color:#00ffff;text-shadow:0 0 20px #00ffff;margin:10px 0}
    .score-label{font-size:12px;color:#888;text-transform:uppercase;letter-spacing:2px}
    .time-display{font-size:24px;color:#ff00ff;text-shadow:0 0 15px #ff00ff;margin-top:15px}
    
    /* Screen 5 - Spectator Feed */
    .spectator-feed{height:100%;overflow-y:auto;font-family:monospace;font-size:11px;line-height:1.6;color:#00ff41}
    .spectator-feed::-webkit-scrollbar{width:4px}
    .spectator-feed::-webkit-scrollbar-track{background:#000}
    .spectator-feed::-webkit-scrollbar-thumb{background:#00ffff;border-radius:2px}
    .spectator-comment{margin-bottom:8px;padding:5px;border-left:2px solid rgba(0,255,255,.3);padding-left:10px;animation:fade-in .5s ease-in}
    @keyframes fade-in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}
    
    /* Screen 6 - System Status */
    .system-status{display:flex;flex-direction:column;gap:12px;height:100%}
    .status-bar{display:flex;align-items:center;gap:10px}
    .status-label{font-size:11px;color:#888;min-width:80px;text-transform:uppercase}
    .status-progress{flex:1;height:8px;background:#000;border:1px solid #00ffff;border-radius:4px;overflow:hidden;position:relative}
    .status-fill{height:100%;background:linear-gradient(90deg,#00ffff,#00ff41);box-shadow:0 0 10px #00ffff;transition:width .3s}
    .status-value{font-size:11px;color:#00ffff;min-width:50px;text-align:right}
    
    /* Control Dashboard */
    .control-dashboard{position:absolute;bottom:0;left:0;right:0;height:180px;background:linear-gradient(to top,#000 0%,rgba(0,0,0,.9) 100%);border-top:3px solid #ff00ff;box-shadow:0 -5px 30px rgba(255,0,255,.5);padding:20px;display:flex;flex-direction:column;gap:15px}
    .dashboard-title{color:#ff00ff;font-size:18px;font-weight:bold;text-transform:uppercase;letter-spacing:3px;text-shadow:0 0 15px #ff00ff;text-align:center;margin-bottom:5px}
    .button-groups{display:flex;justify-content:center;gap:20px;flex-wrap:wrap}
    .button-group{display:flex;flex-direction:column;align-items:center;gap:8px}
    .group-label{font-size:10px;color:#888;text-transform:uppercase;letter-spacing:1px}
    .control-btn{width:70px;height:70px;border-radius:12px;border:3px solid #00ffff;background:linear-gradient(135deg,#0a0a1a 0%,#1a0a1a 100%);color:#00ffff;font-size:11px;font-weight:bold;text-transform:uppercase;cursor:pointer;transition:all .2s;box-shadow:0 0 15px rgba(0,255,255,.3);display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.2;position:relative;overflow:hidden}
    .control-btn::before{content:'';position:absolute;top:50%;left:50%;width:0;height:0;border-radius:50%;background:rgba(0,255,255,.3);transform:translate(-50%,-50%);transition:width .3s,height .3s}
    .control-btn:active::before{width:200px;height:200px}
    .control-btn:hover{border-color:#ff00ff;color:#ff00ff;box-shadow:0 0 25px rgba(255,0,255,.6);transform:translateY(-2px)}
    .control-btn.active{border-color:#00ff41;color:#00ff41;box-shadow:0 0 30px rgba(0,255,65,.8);background:linear-gradient(135deg,#0a1a0a 0%,#1a2a1a 100%)}
    .control-btn.attack{border-color:#ff0040;color:#ff0040}
    .control-btn.attack:hover{box-shadow:0 0 25px rgba(255,0,64,.6)}
    .control-btn.defend{border-color:#0040ff;color:#0040ff}
    .control-btn.defend:hover{box-shadow:0 0 25px rgba(0,64,255,.6)}
    
    /* Battle Mode Selector */
    .mode-selector{position:absolute;top:10px;left:50%;transform:translateX(-50%);display:flex;gap:15px;z-index:10}
    .mode-btn{background:rgba(0,0,0,.8);border:2px solid #ff00ff;color:#ff00ff;padding:10px 20px;border-radius:8px;cursor:pointer;font-size:12px;font-weight:bold;text-transform:uppercase;transition:all .3s;box-shadow:0 0 15px rgba(255,0,255,.3)}
    .mode-btn:hover{background:rgba(26,0,26,.8);box-shadow:0 0 25px rgba(255,0,255,.6);transform:translateY(-2px)}
    .mode-btn.active{background:rgba(255,0,255,.2);border-color:#00ffff;color:#00ffff;box-shadow:0 0 30px rgba(0,255,255,.6)}
    
    /* Exit Button */
    .control-exit-btn{position:absolute;top:10px;left:10px;z-index:100;background:rgba(0,0,0,.9);border:2px solid #f33;color:#f33;padding:8px 20px;border-radius:8px;cursor:pointer;font-size:12px;font-weight:bold;text-transform:uppercase;transition:all .3s;box-shadow:0 0 15px rgba(255,0,64,.3);font-family:monospace}
    .control-exit-btn:hover{background:rgba(51,0,0,.9);border-color:#ff0040;color:#ff0040;box-shadow:0 0 25px rgba(255,0,64,.6);transform:translateY(-2px)}
    .control-exit-btn:active{transform:translateY(0);box-shadow:0 0 15px rgba(255,0,64,.4)}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="ghost-logo">
        <svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="ghostBodyGrad" cx="50%" cy="40%">
              <stop offset="0%" style="stop-color:#0f0;stop-opacity:1" />
              <stop offset="50%" style="stop-color:#0f0;stop-opacity:0.95" />
              <stop offset="100%" style="stop-color:#0a0;stop-opacity:0.9" />
            </radialGradient>
            <radialGradient id="eyeGlow" cx="50%" cy="50%">
              <stop offset="0%" style="stop-color:#0f0;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#0f0;stop-opacity:0" />
            </radialGradient>
            <filter id="outerGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            <filter id="intenseGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <!-- Outer glow aura -->
          <circle cx="100" cy="100" r="85" fill="#0f0" opacity="0.15" filter="url(#intenseGlow)"/>
          
          <!-- Ghost body - sleek, angular, serious -->
          <path d="M 60 50 Q 50 30 100 30 Q 150 30 140 50 L 140 140 Q 140 160 130 170 Q 120 180 100 190 Q 80 180 70 170 Q 60 160 60 140 Z" 
                fill="url(#ghostBodyGrad)" 
                filter="url(#outerGlow)"
                stroke="#0f0" 
                stroke-width="2" 
                opacity="0.95"/>
          
          <!-- Hood/head definition -->
          <path d="M 70 50 Q 60 45 100 45 Q 140 45 130 50" 
                fill="none" 
                stroke="#0f0" 
                stroke-width="1.5" 
                opacity="0.6"/>
          
          <!-- Eyes - intense, glowing -->
          <ellipse cx="85" cy="80" rx="8" ry="12" fill="#000" opacity="0.9"/>
          <ellipse cx="115" cy="80" rx="8" ry="12" fill="#000" opacity="0.9"/>
          
          <!-- Eye glow - piercing -->
          <ellipse cx="85" cy="80" rx="5" ry="8" fill="url(#eyeGlow)" opacity="0.9" filter="url(#outerGlow)"/>
          <ellipse cx="115" cy="80" rx="5" ry="8" fill="url(#eyeGlow)" opacity="0.9" filter="url(#outerGlow)"/>
          
          <!-- Eye highlights -->
          <ellipse cx="87" cy="76" rx="2" ry="3" fill="#0f0" opacity="1"/>
          <ellipse cx="117" cy="76" rx="2" ry="3" fill="#0f0" opacity="1"/>
          
          <!-- Serious expression - subtle, determined -->
          <path d="M 80 100 Q 100 108 120 100" 
                stroke="#000" 
                stroke-width="2.5" 
                fill="none" 
                stroke-linecap="round"
                opacity="0.8"/>
          
          <!-- Hand/arm - sleek, defined -->
          <path d="M 45 85 Q 35 90 30 100 Q 35 110 45 115" 
                fill="#0f0" 
                opacity="0.9" 
                filter="url(#outerGlow)"
                stroke="#0a0" 
                stroke-width="1"/>
          <path d="M 155 85 Q 165 90 170 100 Q 165 110 155 115" 
                fill="#0f0" 
                opacity="0.9" 
                filter="url(#outerGlow)"
                stroke="#0a0" 
                stroke-width="1"/>
          
          <!-- Bottom wavy edge - flowing but controlled -->
          <path d="M 60 140 Q 70 145 80 140 Q 90 145 100 140 Q 110 145 120 140 Q 130 145 140 140" 
                stroke="#0f0" 
                stroke-width="3" 
                fill="none" 
                opacity="0.7"
                filter="url(#outerGlow)"/>
        </svg>
      </div>
      <div class="logo">GHOSTHUD</div>
      <div class="logo-online">ONLINE</div>
      <div>UNIVERSAL 3-PANEL EDITION + SYNC ALL</div>
    </div>

    <div class="status-info">
      <div class="status-item"><div>Role:</div><div id="role">[MASTER NODE]</div></div>
      <div class="status-item"><div>OS:</div><div id="os">Linux</div></div>
      <div class="status-item"><div>Status:</div><div id="status">ONLINE</div></div>
      <div class="status-item"><div>Nodes:</div><div id="node-count">0</div></div>
      <div class="status-item" id="network-mode-item"><div>Network:</div><div id="network-mode">AWAY</div></div>
      <div class="status-item" id="connection-status-item"><div>Connection:</div><div id="connection-status">STANDALONE</div></div>
      <div class="status-item"><div>Tunnel:</div><div id="tunnel-status">OFFLINE</div></div>
    </div>

    <div class="controls">
      <button class="btn" id="menu-btn" onclick="showPage(0)" style="background:#030;box-shadow:0 0 15px #0f0">🏠 MENU</button>
      <button class="btn" id="page1-btn" onclick="showPage(1)">PAGE 1</button>
      <button class="btn" id="page2-btn" onclick="showPage(2)">PAGE 2 - PENTEST</button>
      <button class="btn" id="page3-btn" onclick="showPage(3)">🏛️ COLOSSEUM</button>
      <button class="btn" id="page4-btn" onclick="showPage(4)">🎓 TRAINING</button>
      <button class="btn red" id="control-btn" onclick="takeControl()">TAKE CONTROL</button>
      <button class="btn" id="sync-btn" onclick="syncAll()">SYNC ALL</button>
      <button class="btn" id="start-tunnel-btn" onclick="startTunnel()">START TUNNEL</button>
      <button class="btn red" id="stop-tunnel-btn" onclick="stopTunnel()" style="display:none;">STOP TUNNEL</button>
      <button class="btn blue" id="send-file-btn" onclick="sendFile()">SEND FILE</button>
      <button class="btn" id="plugins-btn" onclick="showPlugins()">PLUGINS</button>
      <button class="btn blue" id="history-btn" onclick="showHistory()">COMMAND HISTORY</button>
      <button class="btn purple" id="auth-btn" onclick="authenticate()">AUTHENTICATE</button>
      <button class="btn" id="injection-mode-btn" onclick="toggleInjectionMode()" style="border-color:#f90;color:#f90">INJECTION: OFF</button>
    </div>

    <!-- MAIN MENU: Landing Page -->
    <div id="page-0" style="display:block">
      <div style="text-align:center;padding:40px;max-width:900px;margin:0 auto">
        <h1 style="color:#0f0;font-size:48px;text-shadow:0 0 20px #0f0;margin-bottom:20px">👻 GHOSTHUD</h1>
        <p style="color:#0f0;font-size:18px;margin-bottom:50px">Select Your Operation</p>
        
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:30px;margin-top:40px">
          <!-- Talk to Ghost -->
          <div class="panel" style="cursor:pointer;transition:all .3s" onclick="showPage(1);Ghost.togglePanel()" onmouseover="this.style.boxShadow='0 0 30px rgba(0,255,65,.6)'" onmouseout="this.style.boxShadow='0 0 15px rgba(0,255,65,.3)'">
            <div class="panel-header" style="font-size:24px">🗣️ TALK TO GHOST</div>
            <div class="panel-body" style="padding:30px;text-align:center">
              <div style="font-size:48px;margin-bottom:15px">👻</div>
              <p>Chat with your AI assistant. Get help, ask questions, or just talk.</p>
            </div>
          </div>
          
          <!-- Pen Testing -->
          <div class="panel" style="cursor:pointer;transition:all .3s" onclick="showPage(2)" onmouseover="this.style.boxShadow='0 0 30px rgba(0,255,65,.6)'" onmouseout="this.style.boxShadow='0 0 15px rgba(0,255,65,.3)'">
            <div class="panel-header" style="font-size:24px">⚔️ PEN TESTING ARSENAL</div>
            <div class="panel-body" style="padding:30px;text-align:center">
              <div style="font-size:48px;margin-bottom:15px">🔧</div>
              <p>Full penetration testing toolkit. Metasploit, Nmap, Burp Suite, and more.</p>
            </div>
          </div>
          
          <!-- Colosseum -->
          <div class="panel" style="cursor:pointer;transition:all .3s" onclick="showPage(3)" onmouseover="this.style.boxShadow='0 0 30px rgba(255,0,0,.6)'" onmouseout="this.style.boxShadow='0 0 15px rgba(255,0,0,.3)'">
            <div class="panel-header" style="font-size:24px;color:#f33">🏛️ COLOSSEUM ARENA</div>
            <div class="panel-body" style="padding:30px;text-align:center">
              <div style="font-size:48px;margin-bottom:15px">⚔️</div>
              <p>Battle system. Practice in sandbox, fight P2P, or challenge the AI champion.</p>
            </div>
          </div>
          
          <!-- Training Facility -->
          <div class="panel" style="cursor:pointer;transition:all .3s" onclick="showPage(4)" onmouseover="this.style.boxShadow='0 0 30px rgba(0,255,255,.6)'" onmouseout="this.style.boxShadow='0 0 15px rgba(0,255,255,.3)'">
            <div class="panel-header" style="font-size:24px;color:#0ff">🎓 TRAINING FACILITY</div>
            <div class="panel-body" style="padding:30px;text-align:center">
              <div style="font-size:48px;margin-bottom:15px">🍯</div>
              <p>Honeypot deployment, agent training, and skill progression challenges.</p>
            </div>
          </div>
        </div>
        
        <div style="margin-top:50px;padding:20px;background:rgba(0,30,0,.3);border:1px solid #0f0;border-radius:10px">
          <p style="color:#0f0;font-size:14px">👑 Developer Mode Active | All Systems Operational</p>
        </div>
      </div>
    </div>
    <!-- END MAIN MENU -->

    <!-- PAGE 1: Main Dashboard -->
    <div id="page-1" style="display:none">
    <div class="panel">
      <div class="panel-header">System Monitor</div>
      <div class="panel-body">
        <div>CPU Usage:</div>
        <div class="progress-bar"><div class="progress" id="cpu-progress" style="width:10%"></div></div>
        <div>Memory Usage:</div>
        <div class="progress-bar"><div class="progress" id="memory-progress" style="width:15%"></div></div>
        <div>Disk Usage:</div>
        <div class="progress-bar"><div class="progress" id="disk-progress" style="width:25%"></div></div>
        <div>Network Traffic:</div>
        <div class="progress-bar"><div class="progress" id="network-progress" style="width:5%"></div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">Network Map</div>
      <div class="panel-body">
        <div id="network-map" class="network-map"></div>
      </div>
    </div>

    <div class="panel" id="file-transfer-panel" style="display:none;">
      <div class="panel-header">File Transfer</div>
      <div class="panel-body">
        <div style="margin-bottom:15px">
          <label style="display:block;margin-bottom:5px">Target Node:</label>
          <select id="target-node-select" style="width:100%;padding:5px;background:#000;color:#0f0;border:1px solid #0f0;font-family:monospace">
            <option value="">Select target node...</option>
          </select>
        </div>
        <div style="margin-bottom:15px">
          <input type="file" id="file-input" style="display:none" onchange="handleFileSelect(event)">
          <button class="btn" onclick="document.getElementById('file-input').click()">Select File...</button>
          <span id="selected-file" style="margin-left:10px;color:#0f0"></span>
          <button class="btn blue" id="send-file-btn-transfer" onclick="startFileTransfer()" style="margin-left:10px;display:none">Send File</button>
        </div>
        <div id="transfer-progress-container" style="display:none">
          <div style="margin-bottom:5px">Transfer Progress:</div>
          <div class="progress-bar">
            <div class="progress" id="transfer-progress" style="width:0%"></div>
          </div>
          <div id="transfer-status" style="margin-top:5px;font-size:12px"></div>
        </div>
        <div id="active-transfers" style="margin-top:15px"></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">Command Output</div>
      <div class="panel-body">
        <pre id="command-output">GhostOps System Initialized
Master Node Online</pre>
      </div>
    </div>

    <div class="tools">
      <div class="tool" onclick="activateTool('port_scanner')">
        <h3>Port Scanner <span style="float:right;font-size:12px;cursor:pointer;color:#33f" onclick="event.stopPropagation();openCodeViewer('port_scanner',{host:'192.168.1.1',ports:[22,80,443,3389,8080]})">&lt;/&gt;</span></h3>
        <p>Scan network for open ports</p>
      </div>
      <div class="tool" onclick="activateTool('packet_sniffer')">
        <h3>Packet Sniffer <span style="float:right;font-size:12px;cursor:pointer;color:#33f" onclick="event.stopPropagation();openCodeViewer('packet_sniffer',{interface:'eth0',count:100})">&lt;/&gt;</span></h3>
        <p>Real-time traffic monitoring</p>
      </div>
      <div class="tool" onclick="activateTool('file_transfer')">
        <h3>File Transfer <span style="float:right;font-size:12px;cursor:pointer;color:#33f" onclick="event.stopPropagation();openCodeViewer('file_transfer',{host:'192.168.1.100',port:8888})">&lt;/&gt;</span></h3>
        <p>Send/Receive files across mesh</p>
      </div>
      <div class="tool" onclick="activateTool('remote_shell')">
        <h3>Remote Shell <span style="float:right;font-size:12px;cursor:pointer;color:#33f" onclick="event.stopPropagation();openCodeViewer('remote_shell',{host:'192.168.1.100',user:'user',port:22})">&lt;/&gt;</span></h3>
        <p>SSH into mesh peers</p>
      </div>
      <div class="tool" onclick="activateTool('exploit_launcher')">
        <h3>Exploit Launcher</h3>
        <p>Deploy payloads to targets</p>
      </div>
      <div class="tool" onclick="activateTool('threat_monitor')">
        <h3>Threat Monitor <span style="float:right;font-size:12px;cursor:pointer;color:#33f" onclick="event.stopPropagation();openCodeViewer('threat_monitor',{})">&lt;/&gt;</span></h3>
        <p>Track intrusions & anomalies</p>
      </div>
      <div class="tool" onclick="activateTool('vuln_scanner')">
        <h3>Vuln Scanner</h3>
        <p>Automated vulnerability scan</p>
      </div>
      <div class="tool" onclick="activateTool('log_analyzer')">
        <h3>Log Analyzer</h3>
        <p>Parse and analyze logs</p>
      </div>
      <div class="tool" style="border-color:#f33;box-shadow:0 0 10px #f33" onclick="crackWifi()">
        <h3 style="color:#f33;text-shadow:0 0 10px #f33">CRACK WIFI <span style="float:right;font-size:12px;cursor:pointer;color:#33f" onclick="event.stopPropagation();openCodeViewer('wifi_scanner',{})">&lt;/&gt;</span></h3>
        <p>Scan & crack nearby networks</p>
      </div>
    </div>
    </div>
    <!-- END PAGE 1 -->

    <!-- PAGE 2: Pentest Arsenal -->
    <div id="page-2" style="display:none">
      <div class="panel">
        <div class="panel-header">🎯 PENETRATION TESTING ARSENAL</div>
        <div class="panel-body">
          <p style="color:#f90;margin-bottom:20px">REAL TOOLS FOR REAL GHOST - Ethical Hacking Suite</p>

          <div class="tools" style="grid-template-columns:repeat(auto-fit,minmax(250px,1fr))">
            <!-- WiFi Cracking -->
            <div class="tool" style="border-color:#f33;box-shadow:0 0 10px #f33" onclick="launchTool('aircrack-ng')">
              <h3 style="color:#f33">Aircrack-ng</h3>
              <p>WiFi security auditing - WEP/WPA/WPA2 cracking</p>
            </div>
            <div class="tool" onclick="launchTool('reaver')">
              <h3>Reaver</h3>
              <p>WPS PIN brute force attack tool</p>
            </div>
            <div class="tool" onclick="launchTool('wifite')">
              <h3>Wifite</h3>
              <p>Automated wireless auditor</p>
            </div>
            <div class="tool" onclick="launchTool('fluxion')">
              <h3>Fluxion</h3>
              <p>Social engineering tool for WiFi</p>
            </div>
            <div class="tool" onclick="launchTool('wifiphisher')">
              <h3>WiFiPhisher</h3>
              <p>Rogue AP framework for WiFi phishing</p>
            </div>
            <div class="tool" onclick="launchTool('airsnarf')">
              <h3>Airsnarf</h3>
              <p>Rogue AP setup tool</p>
            </div>
            <div class="tool" onclick="launchTool('pyrit')">
              <h3>Pyrit</h3>
              <p>GPU-accelerated WPA/WPA2 cracking</p>
            </div>

            <!-- Password Cracking -->
            <div class="tool" onclick="launchTool('john')">
              <h3>John the Ripper</h3>
              <p>Fast password cracker</p>
            </div>
            <div class="tool" onclick="launchTool('hydra')">
              <h3>Hydra</h3>
              <p>Network logon cracker - SSH, FTP, HTTP</p>
            </div>
            <div class="tool" onclick="launchTool('hashcat')">
              <h3>Hashcat</h3>
              <p>World's fastest password cracker</p>
            </div>

            <!-- Network Analysis -->
            <div class="tool" style="border-color:#33f;box-shadow:0 0 10px #33f" onclick="launchTool('bettercap')">
              <h3 style="color:#33f">Bettercap</h3>
              <p>Swiss army knife for network attacks</p>
            </div>
            <div class="tool" onclick="launchTool('wireshark')">
              <h3>Wireshark</h3>
              <p>Network protocol analyzer</p>
            </div>
            <div class="tool" onclick="launchTool('hcxtools')">
              <h3>HCX Tools</h3>
              <p>Portable solution for WiFi security auditing</p>
            </div>

            <!-- OSINT Tools -->
            <div class="tool" style="border-color:#93f;box-shadow:0 0 10px #93f" onclick="launchTool('maltego')">
              <h3 style="color:#93f">Maltego</h3>
              <p>OSINT and graphical link analysis</p>
            </div>
            <div class="tool" onclick="launchTool('pipl')">
              <h3>Pipl</h3>
              <p>People search engine integration</p>
            </div>
            <div class="tool" onclick="launchTool('datasploit')">
              <h3>Data Sploit</h3>
              <p>OSINT framework for reconnaissance</p>
            </div>
            <div class="tool" onclick="launchTool('osintframework')">
              <h3>OSINT Framework</h3>
              <p>Comprehensive OSINT resource</p>
            </div>
            <div class="tool" onclick="launchTool('osintprofiler')">
              <h3>OSINT Profiler</h3>
              <p>Social media reconnaissance</p>
            </div>
            <div class="tool" onclick="launchTool('shadowdragon')">
              <h3>ShadowDragon</h3>
              <p>Social media intelligence platform</p>
            </div>
            <div class="tool" onclick="launchTool('digitalstakeout')">
              <h3>Digital Stakeout</h3>
              <p>Dark web monitoring & OSINT</p>
            </div>
            <div class="tool" onclick="launchTool('irbis')">
              <h3>Irbis Pro</h3>
              <p>Russian OSINT platform</p>
            </div>

            <!-- More Tools -->
            <div class="tool" onclick="launchTool('bullrun')">
              <h3>Bull Run</h3>
              <p>Encryption breaking research tool</p>
            </div>
            <div class="tool" onclick="launchTool('xray')">
              <h3>X-Ray Contact</h3>
              <p>Deep contact tracing system</p>
            </div>
            <div class="tool" onclick="launchTool('espys')">
              <h3>Espys</h3>
              <p>Endpoint surveillance system</p>
            </div>
          </div>

          <div style="margin-top:30px;padding:15px;border:1px solid #f90;background:rgba(40,20,0,.3)">
            <h3 style="color:#f90;margin-bottom:10px">⚠️ ETHICAL USE ONLY</h3>
            <p style="font-size:12px">These tools are for authorized penetration testing and security research only.
            Unauthorized access to computer systems is illegal. Use responsibly with proper documentation.</p>
          </div>
        </div>
      </div>

      <!-- Tool Library (Additional Tools) -->
      <div class="panel">
        <div class="panel-header">📚 TOOL LIBRARY</div>
        <div class="panel-body">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px">
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>Metasploit Framework</strong>
              <p style="font-size:11px;margin-top:5px">Exploitation framework</p>
            </div>
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>Nmap</strong>
              <p style="font-size:11px;margin-top:5px">Network mapper & scanner</p>
            </div>
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>Burp Suite</strong>
              <p style="font-size:11px;margin-top:5px">Web app security testing</p>
            </div>
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>SQLmap</strong>
              <p style="font-size:11px;margin-top:5px">SQL injection automation</p>
            </div>
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>Netcat</strong>
              <p style="font-size:11px;margin-top:5px">Swiss army knife networking</p>
            </div>
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>Nikto</strong>
              <p style="font-size:11px;margin-top:5px">Web server scanner</p>
            </div>
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>Gobuster</strong>
              <p style="font-size:11px;margin-top:5px">Directory/DNS brute forcer</p>
            </div>
            <div style="padding:10px;border:1px solid #0f0;background:rgba(0,20,0,.2)">
              <strong>FFuf</strong>
              <p style="font-size:11px;margin-top:5px">Fast web fuzzer</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Large Output Window for Page 2 -->
      <div class="panel">
        <div class="panel-header">Tool Output</div>
        <div class="panel-body">
          <pre id="page2-output" style="max-height:700px;min-height:500px">Select a tool to begin...</pre>
        </div>
      </div>
    </div>
    <!-- END PAGE 2 -->

    <!-- PAGE 3: GHOSTVERSE CONTROL ROOM -->
    <div id="page-3" style="display:none">
      <div class="control-room">
        <!-- Exit Button -->
        <button class="control-exit-btn" onclick="showPage(0)" title="Return to Main Menu">← EXIT</button>
        
        <!-- Battle Mode Selector -->
        <div class="mode-selector">
          <button class="mode-btn" id="mode-sandbox" onclick="selectBattleMode('sandbox')">🎮 SANDBOX</button>
          <button class="mode-btn" id="mode-p2p" onclick="selectBattleMode('p2p')">👥 P2P BATTLE</button>
          <button class="mode-btn" id="mode-ai" onclick="selectBattleMode('ai')">🤖 VS AI CHAMPION</button>
        </div>
        
        <!-- Neon Frame with 6-Screen Display Wall -->
        <div class="neon-frame">
          <div class="screen-wall">
            <!-- SCREEN 1: OPPONENT AVATAR -->
            <div class="control-screen">
              <div class="screen-header">OPPONENT AVATAR</div>
              <div class="screen-content">
                <div class="opponent-avatar" id="opponent-avatar-screen">
                  <div class="avatar-placeholder">👤</div>
                  <div class="avatar-status" id="opponent-status">WAITING...</div>
                </div>
              </div>
            </div>
            
            <!-- SCREEN 2: 13 GHOSTS HOUSE - Visual Environment -->
            <div class="control-screen">
              <div class="screen-header">13 GHOSTS HOUSE</div>
              <div class="screen-content" style="position:relative;overflow:hidden">
                <canvas id="house-canvas" width="100%" height="100%" style="width:100%;height:100%;background:#0a0a0a"></canvas>
                <div id="house-overlay" style="position:absolute;bottom:5px;left:5px;color:#00ffff;font-size:10px;pointer-events:none">
                  <div>Room: <span id="current-room-display">1</span></div>
                  <div id="house-status">Ready</div>
                </div>
              </div>
            </div>
            
            <!-- SCREEN 3: TECHNIQUE RADAR -->
            <div class="control-screen">
              <div class="screen-header">TECHNIQUE RADAR</div>
              <div class="screen-content">
                <div class="radar-container" id="radar-screen">
                  <div class="radar-circle"></div>
                  <div class="radar-circle"></div>
                  <div class="radar-circle"></div>
                  <div class="radar-center"></div>
                  <canvas id="radar-canvas" width="100%" height="100%" style="width:100%;height:100%;position:absolute;top:0;left:0"></canvas>
                </div>
              </div>
            </div>
            
            <!-- SCREEN 4: SCOREBOARD -->
            <div class="control-screen">
              <div class="screen-header">SCOREBOARD</div>
              <div class="screen-content">
                <div class="scoreboard" id="scoreboard-screen">
                  <div class="score-label">YOUR SCORE</div>
                  <div class="score-display" id="score-you">0</div>
                  <div style="color:#888;font-size:20px;margin:10px 0">VS</div>
                  <div class="score-label">OPPONENT</div>
                  <div class="score-display" id="score-opponent">0</div>
                  <div class="time-display" id="battle-time-display">00:00</div>
                </div>
              </div>
            </div>
            
            <!-- SCREEN 5: SPECTATOR FEED -->
            <div class="control-screen">
              <div class="screen-header">SPECTATOR FEED</div>
              <div class="screen-content">
                <div class="spectator-feed" id="spectator-feed-screen">
                  <div class="spectator-comment">[SYSTEM] Ghostverse Control Room Online</div>
                  <div class="spectator-comment">[SYSTEM] Waiting for battle to begin...</div>
                </div>
              </div>
            </div>
            
            <!-- SCREEN 6: SYSTEM STATUS -->
            <div class="control-screen">
              <div class="screen-header">SYSTEM STATUS</div>
              <div class="screen-content">
                <div class="system-status" id="system-status-screen">
                  <div class="status-bar">
                    <div class="status-label">HEALTH</div>
                    <div class="status-progress"><div class="status-fill" id="health-bar" style="width:100%"></div></div>
                    <div class="status-value" id="health-value">100%</div>
                  </div>
                  <div class="status-bar">
                    <div class="status-label">ENERGY</div>
                    <div class="status-progress"><div class="status-fill" id="energy-bar" style="width:85%"></div></div>
                    <div class="status-value" id="energy-value">85%</div>
                  </div>
                  <div class="status-bar">
                    <div class="status-label">CONNECTION</div>
                    <div class="status-progress"><div class="status-fill" id="connection-bar" style="width:100%"></div></div>
                    <div class="status-value" id="connection-value">STABLE</div>
                  </div>
                  <div class="status-bar">
                    <div class="status-label">TECHNIQUES</div>
                    <div class="status-progress"><div class="status-fill" id="techniques-bar" style="width:0%"></div></div>
                    <div class="status-value" id="techniques-value">0</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- CONTROL DASHBOARD -->
        <div class="control-dashboard">
          <div class="dashboard-title">CONTROL DASHBOARD</div>
          <div class="button-groups">
            <div class="button-group">
              <div class="group-label">ATTACK</div>
              <button class="control-btn attack" onclick="executeAttack('sql_injection')">SQL<br>INJECT</button>
            </div>
            <div class="button-group">
              <div class="group-label">ATTACK</div>
              <button class="control-btn attack" onclick="executeAttack('port_scan')">PORT<br>SCAN</button>
            </div>
            <div class="button-group">
              <div class="group-label">ATTACK</div>
              <button class="control-btn attack" onclick="executeAttack('privilege_escalation')">PRIV<br>ESC</button>
            </div>
            <div class="button-group">
              <div class="group-label">DEFEND</div>
              <button class="control-btn defend" onclick="executeDefense('firewall')">FIRE<br>WALL</button>
            </div>
            <div class="button-group">
              <div class="group-label">DEFEND</div>
              <button class="control-btn defend" onclick="executeDefense('encryption')">ENCRYPT</button>
            </div>
            <div class="button-group">
              <div class="group-label">RECON</div>
              <button class="control-btn" onclick="executeRecon('network_scan')">NET<br>SCAN</button>
            </div>
            <div class="button-group">
              <div class="group-label">RECON</div>
              <button class="control-btn" onclick="executeRecon('vulnerability_scan')">VULN<br>SCAN</button>
            </div>
            <div class="button-group">
              <div class="group-label">DEPLOY</div>
              <button class="control-btn" onclick="executeDeploy('payload')">PAY<br>LOAD</button>
            </div>
            <div class="button-group">
              <div class="group-label">ANALYZE</div>
              <button class="control-btn" onclick="executeAnalyze('traffic')">TRAFFIC</button>
            </div>
            <div class="button-group">
              <div class="group-label">EXECUTE</div>
              <button class="control-btn" onclick="executeCommand()">EXEC</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- END PAGE 3 -->

    <!-- PAGE 4: Training Facility -->
    <div id="page-4" style="display:none">
      <div style="padding:20px">
        <h2 style="color:#0ff;text-align:center;font-size:32px;text-shadow:0 0 15px #0ff;margin-bottom:30px">🎓 TRAINING FACILITY</h2>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
          <!-- Honeypot Controls -->
          <div class="panel">
            <div class="panel-header">🍯 Honeypot System</div>
            <div class="panel-body">
              <button class="btn" onclick="deployHoneypot()" style="width:100%;margin:5px 0;background:#030">DEPLOY HONEYPOT</button>
              <button class="btn" onclick="checkHoneypotStatus()" style="width:100%;margin:5px 0;background:#030">CHECK STATUS</button>
              <button class="btn" onclick="viewHoneypotLogs()" style="width:100%;margin:5px 0;background:#030">VIEW LOGS</button>
              <div id="honeypot-status" style="margin-top:15px;padding:10px;background:rgba(0,30,0,.3);border:1px solid #0f0;border-radius:5px">
                <p style="color:#666">Honeypot: <span id="honeypot-state">OFFLINE</span></p>
              </div>
            </div>
          </div>
          
          <!-- Agent Training -->
          <div class="panel">
            <div class="panel-header">👻 Agent Ghost Training</div>
            <div class="panel-body">
              <button class="btn" onclick="startAgentTraining()" style="width:100%;margin:5px 0;background:#030">START TRAINING</button>
              <button class="btn" onclick="viewTrainingProgress()" style="width:100%;margin:5px 0;background:#030">VIEW PROGRESS</button>
              <button class="btn" onclick="deployAgent()" style="width:100%;margin:5px 0;background:#030">DEPLOY AGENT</button>
              <div id="agent-status" style="margin-top:15px;padding:10px;background:rgba(0,30,0,.3);border:1px solid #0f0;border-radius:5px">
                <p style="color:#666">Agent: <span id="agent-state">IDLE</span></p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Training Output -->
        <div class="panel" style="min-height:400px">
          <div class="panel-header">Training Output</div>
          <div class="panel-body">
            <pre id="training-output" style="max-height:500px;overflow-y:auto;background:#000;color:#0f0;padding:15px;border:1px solid #0f0;border-radius:5px;font-family:monospace">Ready for training operations...</pre>
          </div>
        </div>
        
        <!-- Challenge Rooms -->
        <div class="panel">
          <div class="panel-header">Challenge Rooms</div>
          <div class="panel-body">
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px">
              <button class="btn" onclick="enterChallengeRoom(1)" style="background:#030">ROOM 1: Easy Scan</button>
              <button class="btn" onclick="enterChallengeRoom(2)" style="background:#030">ROOM 2: Escalation</button>
              <button class="btn" onclick="enterChallengeRoom(3)" style="background:#030">ROOM 3: Data Access</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- END PAGE 4 -->

  </div>

  <div class="notification" id="notification"></div>

  <!-- Code Viewer Modal - BIGGER (800x700) -->
  <div id="code-viewer-modal" class="code-viewer-modal">
    <div class="code-viewer-header">
      <div class="code-viewer-title" id="code-viewer-title">Port Scanner</div>
      <button class="code-viewer-close" onclick="closeCodeViewer()">X CLOSE</button>
    </div>
    <div class="code-viewer-tabs">
      <button class="code-viewer-tab active" onclick="switchCodeTab('python')">PYTHON</button>
      <button class="code-viewer-tab" onclick="switchCodeTab('windows')">WINDOWS</button>
      <button class="code-viewer-tab" onclick="switchCodeTab('termux')">TERMUX</button>
    </div>
    <div class="code-viewer-content">
      <div id="code-panel-python" class="code-viewer-panel active">
        <div id="code-warning-python" class="code-warning" style="display:none"></div>
        <pre class="code-viewer-code" id="code-output-python"># Python code will appear here</pre>
      </div>
      <div id="code-panel-termux" class="code-viewer-panel">
        <div id="code-warning-termux" class="code-warning" style="display:none"></div>
        <pre class="code-viewer-code" id="code-output-termux"># Termux code will appear here</pre>
      </div>
      <div id="code-panel-windows" class="code-viewer-panel">
        <div id="code-warning-windows" class="code-warning" style="display:none"></div>
        <pre class="code-viewer-code" id="code-output-windows"># Windows code will appear here</pre>
      </div>
    </div>
    <div class="code-viewer-actions">
      <button class="code-viewer-btn" onclick="copyCodeToClipboard()">COPY TO CLIPBOARD</button>
      <button class="code-viewer-btn run" onclick="runCurrentCode()">RUN</button>
    </div>
  </div>

  <!-- WiFi Crack Panel -->
  <div id="wifi-panel" style="display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:90%;max-width:800px;background:#000;border:2px solid #f33;padding:20px;z-index:10000;box-shadow:0 0 30px #f33">
    <div style="text-align:center;margin-bottom:20px">
      <h2 style="color:#f33;text-shadow:0 0 15px #f33;margin:0">WI-FI CRACKER</h2>
      <div style="color:#0f0;font-size:12px;margin-top:5px">DEMO MODE</div>
    </div>
    <div id="wifi-progress" style="color:#f33;text-align:center;min-height:100px;display:flex;align-items:center;justify-content:center;flex-direction:column">
      <div style="font-size:48px;margin-bottom:20px">...SCANNING...</div>
    </div>
    <button class="btn" onclick="document.getElementById('wifi-panel').style.display='none'" style="width:100%;margin-top:20px">CLOSE</button>
  </div>
  
  <!-- Tool Output Modal -->
  <div id="tool-output-modal" class="tool-output-modal">
    <div class="tool-modal-header">
      <div class="tool-modal-title" id="tool-modal-title">Tool Output</div>
      <button class="tool-modal-close" onclick="closeToolModal()">CLOSE</button>
    </div>
    <div class="tool-modal-tabs">
      <button class="tool-modal-tab active" onclick="switchToolTab('output')">OUTPUT</button>
      <button class="tool-modal-tab" onclick="switchToolTab('code')">CODE</button>
    </div>
    <div class="tool-modal-content">
      <div id="tool-output-panel" class="tool-modal-panel active">
        <div class="tool-result-output" id="tool-result-output">Waiting for tool execution...</div>
      </div>
      <div id="tool-code-panel" class="tool-modal-panel">
        <div class="tool-code-selector">
          <label>View Code As:</label>
          <select id="tool-code-language" onchange="updateToolCode()">
            <option value="python">Python</option>
            <option value="bash">Bash</option>
            <option value="termux">Termux</option>
          </select>
        </div>
        <div class="tool-code-output" id="tool-code-output">Select a tool to view code...</div>
      </div>
    </div>
  </div>

  <script>
    // Global state
    // DEVELOPER MODE: Auto-authenticate as KingKali
    let authenticated = true;  // Always authenticated in dev mode
    console.log('👑 Developer Mode: Auto-authenticated as KingKali');
    let currentTool = null;
    let lastSync = Date.now();
    
    // Utilities
    function showNotification(message) {
      const notification = document.getElementById('notification');
      notification.textContent = message;
      notification.classList.add('show');
      setTimeout(() => notification.classList.remove('show'), 3000);
    }
    
    function log(message) {
      const output = document.getElementById('command-output');
      output.textContent += "\\n" + message;
      output.scrollTop = output.scrollHeight;
    }

    // Code Viewer Modal Functions
    let currentCodeTab = 'python';
    let currentCodeTool = null;
    let currentCodeParams = null;

    function openCodeViewer(toolName, params = {}) {
      currentCodeTool = toolName;
      currentCodeParams = params;

      // Clear all warnings first
      document.getElementById('code-warning-python').style.display = 'none';
      document.getElementById('code-warning-termux').style.display = 'none';
      document.getElementById('code-warning-windows').style.display = 'none';

      // Set title
      const titleMap = {
        'port_scanner': 'Port Scanner',
        'packet_sniffer': 'Packet Sniffer',
        'file_transfer': 'File Transfer',
        'remote_shell': 'Remote Shell / SSH',
        'threat_monitor': 'Threat Monitor',
        'wifi_scanner': 'WiFi Scanner'
      };
      document.getElementById('code-viewer-title').textContent = titleMap[toolName] || toolName.toUpperCase();

      // Generate code for all tabs
      generateCodeForTool(toolName, params);

      // Show modal
      document.getElementById('code-viewer-modal').classList.add('active');

      // Switch to Python tab by default
      switchCodeTab('python');
    }

    function closeCodeViewer() {
      document.getElementById('code-viewer-modal').classList.remove('active');
      currentCodeTool = null;
      currentCodeParams = null;
    }

    function switchCodeTab(tab) {
      currentCodeTab = tab;

      // Update tab buttons
      const tabs = document.querySelectorAll('.code-viewer-tab');
      tabs.forEach(btn => btn.classList.remove('active'));

      // Update panels
      document.getElementById('code-panel-python').classList.remove('active');
      document.getElementById('code-panel-termux').classList.remove('active');
      document.getElementById('code-panel-windows').classList.remove('active');

      if (tab === 'python') {
        document.getElementById('code-panel-python').classList.add('active');
        tabs[0].classList.add('active');
      } else if (tab === 'windows') {
        document.getElementById('code-panel-windows').classList.add('active');
        tabs[1].classList.add('active');
      } else if (tab === 'termux') {
        document.getElementById('code-panel-termux').classList.add('active');
        tabs[2].classList.add('active');
      }
    }

    function copyCodeToClipboard() {
      const codeElement = document.getElementById('code-output-' + currentCodeTab);
      const code = codeElement.textContent;

      navigator.clipboard.writeText(code).then(() => {
        showNotification('Code copied to clipboard!');
      }).catch(err => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = code;
        document.body.appendChild(textArea);
        textArea.select();
        try {
          document.execCommand('copy');
          showNotification('Code copied to clipboard!');
        } catch (err) {
          showNotification('Failed to copy code');
        }
        document.body.removeChild(textArea);
      });
    }

    function runCurrentCode() {
      showNotification('RUN feature - Execute code via backend API (not implemented in demo)');
      log('[INFO] RUN button clicked - would execute ' + currentCodeTab + ' code for ' + currentCodeTool);
    }

    function generateCodeForTool(toolName, params) {
      if (toolName === 'port_scanner') {
        generatePortScannerCode(params);
      } else if (toolName === 'packet_sniffer') {
        generatePacketSnifferCode(params);
      } else if (toolName === 'file_transfer') {
        generateFileTransferCode(params);
      } else if (toolName === 'remote_shell') {
        generateRemoteShellCode(params);
      } else if (toolName === 'threat_monitor') {
        generateThreatMonitorCode(params);
      } else if (toolName === 'wifi_scanner') {
        generateWifiScannerCode(params);
      }
    }

    function generatePortScannerCode(params) {
      const host = params.host || '192.168.1.1';
      const ports = params.ports || [21, 22, 23, 80, 443, 3306, 8080];
      const startPort = params.start_port || null;
      const endPort = params.end_port || null;

      // Python code
      let pythonCode = `#!/usr/bin/env python3
# Port Scanner - Python Implementation
import socket
import sys
from datetime import datetime

def scan_port(host, port, timeout=1.0):
    # Scan a single port on the target host
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def main():
    host = "${host}"
    print(f"[*] Starting port scan on {host}")
    print(f"[*] Scan started at {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)

    open_ports = []
    `;

      if (startPort && endPort) {
        pythonCode += `ports_to_scan = range(${startPort}, ${endPort + 1})
    `;
      } else {
        pythonCode += `ports_to_scan = [${ports.join(', ')}]
    `;
      }

      pythonCode += `
    for port in ports_to_scan:
        if scan_port(host, port):
            print(f"[+] Port {port}: OPEN")
            open_ports.append(port)
        else:
            print(f"[-] Port {port}: CLOSED")

    print("-" * 50)
    print(f"[*] Scan completed at {datetime.now().strftime('%H:%M:%S')}")
    print(f"[*] Found {len(open_ports)} open ports: {', '.join(map(str, open_ports))}")

if __name__ == "__main__":
    main()
`;

      // Termux code
      let termuxCode = `#!/data/data/com.termux/files/usr/bin/bash
# Port Scanner - Termux Implementation

# Install required packages
echo "[*] Installing nmap..."
pkg install nmap -y

# Run scan
HOST="${host}"
`;

      if (startPort && endPort) {
        termuxCode += `PORTS="${startPort}-${endPort}"
`;
      } else {
        termuxCode += `PORTS="${ports.join(',')}"
`;
      }

      termuxCode += `
echo "[*] Starting port scan on $HOST"
echo "[*] Ports: $PORTS"
echo "----------------------------------------"

nmap -p $PORTS $HOST --open

echo "----------------------------------------"
echo "[*] Scan complete"
`;

      // Linux code
      let windowsCode = `# PowerShell
# Port Scanner - Linux Implementation

HOST="${host}"
TIMEOUT=1
`;

      if (startPort && endPort) {
        windowsCode += `START_PORT=${startPort}
END_PORT=${endPort}

echo "[*] Starting port scan on $HOST"
echo "[*] Port range: $START_PORT-$END_PORT"
echo "----------------------------------------"

for port in $(seq $START_PORT $END_PORT); do
    (timeout $TIMEOUT bash -c "echo >/dev/tcp/$HOST/$port" 2>/dev/null) && \\
        echo "[+] Port $port: OPEN" || \\
        echo "[-] Port $port: CLOSED"
done
`;
      } else {
        windowsCode += `PORTS=(${ports.join(' ')})

echo "[*] Starting port scan on $HOST"
echo "[*] Scanning ${ports.length} ports"
echo "----------------------------------------"

for port in "\\${PORTS[@]}"; do
    (timeout $TIMEOUT bash -c "echo >/dev/tcp/$HOST/$port" 2>/dev/null) && \\
        echo "[+] Port $port: OPEN" || \\
        echo "[-] Port $port: CLOSED"
done
`;
      }

      windowsCode += `
echo "----------------------------------------"
echo "[*] Scan complete"
`;

      document.getElementById('code-output-python').textContent = pythonCode;
      document.getElementById('code-output-termux').textContent = termuxCode;
      document.getElementById('code-output-windows').textContent = windowsCode;
    }

    function generatePacketSnifferCode(params) {
      const iface = params.interface || 'eth0';
      const count = params.count || 100;

      // Python code
      const pythonCode = `#!/usr/bin/env python3
# Packet Sniffer - Python Implementation
# Requires: scapy

try:
    from scapy.all import sniff, IP, TCP, UDP, Raw
except ImportError:
    print("[!] Please install scapy: pip install scapy")
    exit(1)

def packet_handler(packet):
    # Handle captured packets
    if IP in packet:
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        protocol = packet[IP].proto

        print(f"[+] {ip_src} -> {ip_dst} (Protocol: {protocol})")

        if TCP in packet:
            print(f"    TCP: {packet[TCP].sport} -> {packet[TCP].dport}")
        elif UDP in packet:
            print(f"    UDP: {packet[UDP].sport} -> {packet[UDP].dport}")

        if Raw in packet:
            payload = packet[Raw].load[:50]
            print(f"    Data: {payload}")

def main():
    interface = "${iface}"
    count = ${count}

    print(f"[*] Starting packet capture on {interface}")
    print(f"[*] Capturing {count} packets...")
    print("-" * 50)

    try:
        sniff(iface=interface, prn=packet_handler, count=count)
    except PermissionError:
        print("[!] Permission denied. Run with sudo.")
    except Exception as e:
        print(f"[!] Error: {e}")

    print("-" * 50)
    print("[*] Capture complete")

if __name__ == "__main__":
    main()
`;

      // Termux code
      const termuxCode = `#!/data/data/com.termux/files/usr/bin/bash
# Packet Sniffer - Termux Implementation

echo "[!] WARNING: Packet sniffing on Android requires root access"
echo "[!] This may not work on non-rooted devices"
echo ""

# Install tcpdump
echo "[*] Installing tcpdump..."
pkg install tcpdump root-repo -y

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run with root privileges (su)"
    echo "[*] Attempting to run with su..."
    su -c "tcpdump -i any -c ${count} -n"
else
    echo "[*] Starting packet capture..."
    tcpdump -i any -c ${count} -n
fi

echo "[*] Capture complete"
`;

      // Linux code
      const windowsCode = `# PowerShell
# Packet Sniffer - Linux Implementation

INTERFACE="${iface}"
COUNT=${count}

echo "[*] Starting packet capture on $INTERFACE"
echo "[*] Capturing $COUNT packets..."
echo "----------------------------------------"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run as root (sudo)"
    exit 1
fi

# Install tcpdump if not available
if ! command -v tcpdump &> /dev/null; then
    echo "[*] Installing tcpdump..."
    apt-get update && apt-get install -y tcpdump
fi

# Capture packets
tcpdump -i $INTERFACE -c $COUNT -n -v

echo "----------------------------------------"
echo "[*] Capture complete"
`;

      document.getElementById('code-output-python').textContent = pythonCode;
      document.getElementById('code-output-termux').textContent = termuxCode;
      document.getElementById('code-output-windows').textContent = windowsCode;

      // Show warnings
      document.getElementById('code-warning-python').textContent = '⚠ Requires root/admin privileges and scapy library';
      document.getElementById('code-warning-python').style.display = 'block';
      document.getElementById('code-warning-termux').textContent = '⚠ Requires root access on Android device';
      document.getElementById('code-warning-termux').style.display = 'block';
      document.getElementById('code-warning-windows').textContent ='⚠ Requires root privileges (run with sudo)';
      document.getElementById('code-warning-windows').style.display ='block';
    }

    function generateFileTransferCode(params) {
      const host = params.host || '192.168.1.100';
      const port = params.port || 8888;
      const file = params.file || 'document.txt';

      // Python code
      const pythonCode = `#!/usr/bin/env python3
# File Transfer - Python Implementation

import socket
import os
import sys

def send_file(host, port, filepath):
    # Send file to remote host
    try:
        # Get file size
        file_size = os.path.getsize(filepath)

        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        print(f"[*] Connected to {host}:{port}")
        print(f"[*] Sending file: {filepath} ({file_size} bytes)")

        # Send filename and size
        filename = os.path.basename(filepath)
        sock.send(f"{filename}|{file_size}".encode())

        # Wait for acknowledgment
        ack = sock.recv(1024).decode()
        if ack != "READY":
            print("[!] Server not ready")
            return

        # Send file data
        with open(filepath, 'rb') as f:
            sent = 0
            while True:
                data = f.read(4096)
                if not data:
                    break
                sock.send(data)
                sent += len(data)
                progress = (sent / file_size) * 100
                print(f"\\r[*] Progress: {progress:.1f}%", end='')

        print("\\n[+] File sent successfully")
        sock.close()

    except Exception as e:
        print(f"[!] Error: {e}")

def receive_file(port):
    # Receive file from remote host
    try:
        # Create server socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', port))
        server.listen(1)

        print(f"[*] Listening on port {port}...")

        conn, addr = server.accept()
        print(f"[*] Connection from {addr}")

        # Receive filename and size
        header = conn.recv(1024).decode()
        filename, file_size = header.split('|')
        file_size = int(file_size)

        print(f"[*] Receiving: {filename} ({file_size} bytes)")

        # Send acknowledgment
        conn.send(b"READY")

        # Receive file data
        with open(filename, 'wb') as f:
            received = 0
            while received < file_size:
                data = conn.recv(4096)
                if not data:
                    break
                f.write(data)
                received += len(data)
                progress = (received / file_size) * 100
                print(f"\\r[*] Progress: {progress:.1f}%", end='')

        print("\\n[+] File received successfully")
        conn.close()
        server.close()

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Send: python3 script.py send <host> <port> <file>")
        print("  Receive: python3 script.py receive <port>")
        exit(1)

    mode = sys.argv[1]

    if mode == "send":
        if len(sys.argv) != 5:
            print("Usage: python3 script.py send <host> <port> <file>")
            exit(1)
        send_file(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif mode == "receive":
        if len(sys.argv) != 3:
            print("Usage: python3 script.py receive <port>")
            exit(1)
        receive_file(int(sys.argv[2]))
`;

      // Termux code
      const termuxCode = `#!/data/data/com.termux/files/usr/bin/bash
# File Transfer - Termux Implementation

# Install required packages
pkg install python netcat-openbsd -y

# Simple file transfer using netcat
HOST="${host}"
PORT=${port}
FILE="${file}"

echo "[*] File Transfer Tool"
echo ""
echo "Select mode:"
echo "1) Send file"
echo "2) Receive file"
read -p "Choice: " choice

if [ "$choice" = "1" ]; then
    read -p "Enter file path: " filepath
    read -p "Enter destination host: " host
    read -p "Enter port [${port}]: " port
    port=\\${port:-${port}}

    if [ -f "$filepath" ]; then
        echo "[*] Sending $filepath to $host:$port..."
        cat "$filepath" | nc $host $port
        echo "[+] Transfer complete"
    else
        echo "[!] File not found: $filepath"
    fi

elif [ "$choice" = "2" ]; then
    read -p "Enter port to listen on [${port}]: " port
    port=\\${port:-${port}}
    read -p "Enter output filename: " output

    echo "[*] Listening on port $port..."
    echo "[*] Waiting for connection..."
    nc -l -p $port > "$output"
    echo "[+] File received: $output"
else
    echo "[!] Invalid choice"
fi
`;

      // Linux code
      const windowsCode = `# PowerShell
# File Transfer - Linux Implementation

HOST="${host}"
PORT=${port}

echo "[*] File Transfer Tool"
echo ""
echo "Select mode:"
echo "1) Send file (using netcat)"
echo "2) Receive file (using netcat)"
echo "3) Send file (using scp)"
echo "4) Start HTTP server"
read -p "Choice: " choice

case $choice in
    1)
        read -p "Enter file path: " filepath
        read -p "Enter destination host [$HOST]: " host
        host=\\${host:-$HOST}
        read -p "Enter port [$PORT]: " port
        port=\\${port:-$PORT}

        if [ -f "$filepath" ]; then
            echo "[*] Sending $filepath to $host:$port..."
            cat "$filepath" | nc $host $port
            echo "[+] Transfer complete"
        else
            echo "[!] File not found: $filepath"
        fi
        ;;
    2)
        read -p "Enter port to listen on [$PORT]: " port
        port=\\${port:-$PORT}
        read -p "Enter output filename: " output

        echo "[*] Listening on port $port..."
        nc -l -p $port > "$output"
        echo "[+] File received: $output"
        ;;
    3)
        read -p "Enter file path: " filepath
        read -p "Enter destination (user@host:/path): " dest

        if [ -f "$filepath" ]; then
            echo "[*] Transferring via SCP..."
            scp "$filepath" "$dest"
            echo "[+] Transfer complete"
        else
            echo "[!] File not found: $filepath"
        fi
        ;;
    4)
        read -p "Enter port to serve on [8000]: " port
        port=\\${port:-8000}

        echo "[*] Starting HTTP server on port $port..."
        echo "[*] Files available at: http://$(hostname -I | awk '{print $1}'):$port"
        python3 -m http.server $port
        ;;
    *)
        echo "[!] Invalid choice"
        ;;
esac
`;

      document.getElementById('code-output-python').textContent = pythonCode;
      document.getElementById('code-output-termux').textContent = termuxCode;
      document.getElementById('code-output-windows').textContent = windowsCode;
    }

    function generateRemoteShellCode(params) {
      const host = params.host || '192.168.1.100';
      const user = params.user || 'user';
      const port = params.port || 22;

      // Python code
      const pythonCode = `#!/usr/bin/env python3
# Remote Shell / SSH - Python Implementation

import subprocess
import sys

def ssh_connect(host, username, port=22, command=None):
    # Connect via SSH and execute command
    try:
        if command:
            # Execute single command
            ssh_cmd = ['ssh', f'{username}@{host}', '-p', str(port), command]
            result = subprocess.run(ssh_cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}", file=sys.stderr)
            return result.returncode
        else:
            # Interactive shell
            ssh_cmd = ['ssh', f'{username}@{host}', '-p', str(port)]
            subprocess.run(ssh_cmd)
    except Exception as e:
        print(f"[!] Error: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Interactive: python3 script.py <host> <username> [port]")
        print("  Command: python3 script.py <host> <username> <command> [port]")
        exit(1)

    host = sys.argv[1]
    username = sys.argv[2]

    if len(sys.argv) > 3 and not sys.argv[3].isdigit():
        command = sys.argv[3]
        port = int(sys.argv[4]) if len(sys.argv) > 4 else 22
    else:
        command = None
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 22

    print(f"[*] Connecting to {username}@{host}:{port}")
    ssh_connect(host, username, port, command)
`;

      // Termux code
      const termuxCode = `#!/data/data/com.termux/files/usr/bin/bash
# Remote Shell / SSH - Termux Implementation

# Install OpenSSH
echo "[*] Installing OpenSSH..."
pkg install openssh -y

HOST="${host}"
USER="${user}"
PORT=${port}

echo "[*] SSH Remote Shell Tool"
echo ""
echo "Select mode:"
echo "1) Connect to remote host (SSH client)"
echo "2) Start SSH server (allow incoming)"
echo "3) Execute single command"
read -p "Choice: " choice

case $choice in
    1)
        read -p "Enter host [$HOST]: " host
        host=\\${host:-$HOST}
        read -p "Enter username [$USER]: " user
        user=\\${user:-$USER}
        read -p "Enter port [$PORT]: " port
        port=\\${port:-$PORT}

        echo "[*] Connecting to $user@$host:$port..."
        ssh -p $port $user@$host
        ;;
    2)
        echo "[*] Starting SSH server..."
        echo "[*] First, set a password with 'passwd'"
        echo "[*] Your device IP: $(ifconfig wlan0 | grep 'inet ' | awk '{print $2}')"
        echo ""
        sshd -p 8022
        echo "[+] SSH server started on port 8022"
        echo "[*] Connect with: ssh -p 8022 $(whoami)@$(ifconfig wlan0 | grep 'inet ' | awk '{print $2}')"
        ;;
    3)
        read -p "Enter host [$HOST]: " host
        host=\\${host:-$HOST}
        read -p "Enter username [$USER]: " user
        user=\\${user:-$USER}
        read -p "Enter command: " cmd

        echo "[*] Executing command on $user@$host..."
        ssh $user@$host "$cmd"
        ;;
    *)
        echo "[!] Invalid choice"
        ;;
esac
`;

      // Linux code
      const windowsCode = `# PowerShell
# Remote Shell / SSH - Linux Implementation

HOST="${host}"
USER="${user}"
PORT=${port}

echo "[*] SSH Remote Shell Tool"
echo ""
echo "Select mode:"
echo "1) Connect to remote host"
echo "2) Execute single command"
echo "3) Copy SSH key to remote host"
echo "4) Start reverse SSH tunnel"
read -p "Choice: " choice

case $choice in
    1)
        read -p "Enter host [$HOST]: " host
        host=\\${host:-$HOST}
        read -p "Enter username [$USER]: " user
        user=\\${user:-$USER}
        read -p "Enter port [$PORT]: " port
        port=\\${port:-$PORT}

        echo "[*] Connecting to $user@$host:$port..."
        ssh -p $port $user@$host
        ;;
    2)
        read -p "Enter host [$HOST]: " host
        host=\\${host:-$HOST}
        read -p "Enter username [$USER]: " user
        user=\\${user:-$USER}
        read -p "Enter command: " cmd

        echo "[*] Executing: $cmd"
        ssh $user@$host "$cmd"
        ;;
    3)
        read -p "Enter host [$HOST]: " host
        host=\\${host:-$HOST}
        read -p "Enter username [$USER]: " user
        user=\\${user:-$USER}

        echo "[*] Copying SSH key to $user@$host..."

        if [ ! -f ~/.ssh/id_rsa.pub ]; then
            echo "[*] Generating SSH key..."
            ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
        fi

        ssh-copy-id $user@$host
        echo "[+] SSH key copied. You can now login without password."
        ;;
    4)
        read -p "Enter remote host [$HOST]: " host
        host=\\${host:-$HOST}
        read -p "Enter username [$USER]: " user
        user=\\${user:-$USER}
        read -p "Enter remote port to bind [8080]: " rport
        rport=\\${rport:-8080}
        read -p "Enter local port to forward [22]: " lport
        lport=\\${lport:-22}

        echo "[*] Starting reverse tunnel..."
        echo "[*] Remote port $rport -> Local port $lport"
        ssh -R $rport:localhost:$lport $user@$host -N
        ;;
    *)
        echo "[!] Invalid choice"
        ;;
esac
`;

      document.getElementById('code-output-python').textContent = pythonCode;
      document.getElementById('code-output-termux').textContent = termuxCode;
      document.getElementById('code-output-windows').textContent = windowsCode;
    }

    function generateThreatMonitorCode(params) {
      // Python code
      const pythonCode = `#!/usr/bin/env python3
# Threat Monitor - Python Implementation

import psutil
import time
from datetime import datetime
from collections import defaultdict

class ThreatMonitor:
    def __init__(self):
        self.connection_counts = defaultdict(int)
        self.suspicious_ports = [4444, 1337, 31337, 6666, 12345]
        self.alerts = []

    def check_connections(self):
        # Monitor network connections for suspicious activity
        connections = psutil.net_connections()

        for conn in connections:
            if conn.status == 'ESTABLISHED':
                remote_addr = conn.raddr
                if remote_addr:
                    # Check for suspicious ports
                    if remote_addr.port in self.suspicious_ports:
                        self.add_alert('HIGH',
                            f'Suspicious port detected: {remote_addr.ip}:{remote_addr.port}')

                    # Track connection frequency
                    self.connection_counts[remote_addr.ip] += 1

    def check_processes(self):
        # Monitor running processes for suspicious activity
        suspicious_names = ['nc', 'netcat', 'ncat', 'backdoor', 'reverse']

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()

                for sus in suspicious_names:
                    if sus in name or sus in cmdline:
                        self.add_alert('MEDIUM',
                            f'Suspicious process: {proc.info["name"]} (PID: {proc.info["pid"]})')
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def check_high_frequency_connections(self):
        # Detect potential DDoS or scanning activity
        for ip, count in self.connection_counts.items():
            if count > 50:
                self.add_alert('HIGH',
                    f'High frequency connections from {ip}: {count} connections')

    def add_alert(self, severity, message):
        # Add alert to the list
        alert = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'severity': severity,
            'message': message
        }
        self.alerts.append(alert)
        self.print_alert(alert)

    def print_alert(self, alert):
        # Print alert to console
        color = {
            'HIGH': '\\\\033[91m',
            'MEDIUM': '\\\\033[93m',
            'LOW': '\\\\033[92m'
        }.get(alert['severity'], '')
        reset = '\\\\033[0m'

        print(f"{color}[{alert['timestamp']}] [{alert['severity']}] {alert['message']}{reset}")

    def monitor(self, duration=60, interval=5):
        # Run continuous monitoring
        print(f"[*] Starting threat monitor for {duration} seconds...")
        print(f"[*] Check interval: {interval} seconds")
        print("-" * 60)

        start_time = time.time()

        while time.time() - start_time < duration:
            self.connection_counts.clear()

            self.check_connections()
            self.check_processes()
            self.check_high_frequency_connections()

            time.sleep(interval)

        print("-" * 60)
        print(f"[*] Monitoring complete. Total alerts: {len(self.alerts)}")

        # Summary
        high = sum(1 for a in self.alerts if a['severity'] == 'HIGH')
        medium = sum(1 for a in self.alerts if a['severity'] == 'MEDIUM')
        low = sum(1 for a in self.alerts if a['severity'] == 'LOW')

        print(f"[*] Severity breakdown: HIGH={high}, MEDIUM={medium}, LOW={low}")

if __name__ == "__main__":
    monitor = ThreatMonitor()
    try:
        monitor.monitor(duration=300, interval=5)  # 5 minutes
    except KeyboardInterrupt:
        print("\\n[*] Monitoring stopped by user")
`;

      // Termux code
      const termuxCode = `#!/data/data/com.termux/files/usr/bin/bash
# Threat Monitor - Termux Implementation

# Install required packages
pkg install net-tools procps -y

echo "[*] Threat Monitoring Tool"
echo "[*] Monitoring network connections and processes..."
echo "----------------------------------------"

DURATION=300  # 5 minutes
INTERVAL=5

start_time=$(date +%s)
alert_count=0

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))

    if [ $elapsed -ge $DURATION ]; then
        break
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking for threats..."

    # Check for established connections
    netstat -an | grep ESTABLISHED | while read line; do
        port=$(echo $line | awk '{print $5}' | cut -d: -f2)

        # Check for suspicious ports
        case $port in
            4444|1337|31337|6666|12345)
                echo "[HIGH] Suspicious port detected: $port"
                alert_count=$((alert_count + 1))
                ;;
        esac
    done

    # Check for suspicious processes
    ps aux | grep -iE '(nc|netcat|ncat|backdoor|reverse)' | grep -v grep | while read line; do
        echo "[MEDIUM] Suspicious process: $line"
        alert_count=$((alert_count + 1))
    done

    sleep $INTERVAL
done

echo "----------------------------------------"
echo "[*] Monitoring complete"
echo "[*] Total alerts: $alert_count"
`;

      // Linux code
      const windowsCode = `# PowerShell
# Threat Monitor - Linux Implementation

echo "[*] Threat Monitoring Tool"
echo "[*] Monitoring for suspicious activity..."
echo "----------------------------------------"

DURATION=300  # 5 minutes
INTERVAL=5
LOG_FILE="/tmp/threat_monitor_$(date +%Y%m%d_%H%M%S).log"

start_time=$(date +%s)
alert_count=0

log_alert() {
    severity=$1
    message=$2
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$severity] $message" | tee -a "$LOG_FILE"
    alert_count=$((alert_count + 1))
}

monitor_connections() {
    # Check for suspicious established connections
    netstat -antp 2>/dev/null | grep ESTABLISHED | while read line; do
        remote=$(echo $line | awk '{print $5}')
        port=$(echo $remote | cut -d: -f2)

        # Suspicious ports
        case $port in
            4444|1337|31337|6666|12345|8888|9999)
                log_alert "HIGH" "Suspicious port connection: $remote"
                ;;
        esac
    done
}

monitor_processes() {
    # Check for suspicious processes
    ps aux | grep -iE '(nc|netcat|ncat|socat|backdoor|reverse|meterpreter)' | grep -v grep | while read line; do
        pid=$(echo $line | awk '{print $2}')
        cmd=$(echo $line | awk '{print $11}')
        log_alert "MEDIUM" "Suspicious process detected: $cmd (PID: $pid)"
    done
}

monitor_files() {
    # Check for recently modified system files
    find /etc /usr/bin /usr/sbin -type f -mmin -5 2>/dev/null | while read file; do
        log_alert "LOW" "Recently modified system file: $file"
    done
}

monitor_users() {
    # Check for active user sessions
    who | while read line; do
        user=$(echo $line | awk '{print $1}')
        tty=$(echo $line | awk '{print $2}')
        from=$(echo $line | awk '{print $5}')

        if [ ! -z "$from" ]; then
            echo "[INFO] Active session: $user on $tty from $from"
        fi
    done
}

# Main monitoring loop
while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))

    if [ $elapsed -ge $DURATION ]; then
        break
    fi

    echo "[$(date '+%H:%M:%S')] Running threat checks..."

    monitor_connections
    monitor_processes
    monitor_files
    monitor_users

    sleep $INTERVAL
done

echo "----------------------------------------"
echo "[*] Monitoring complete"
echo "[*] Total alerts: $alert_count"
echo "[*] Log saved to: $LOG_FILE"

# Generate summary
echo ""
echo "[*] Alert Summary:"
grep "\\[HIGH\\]" "$LOG_FILE" 2>/dev/null | wc -l | xargs echo "HIGH severity alerts:"
grep "\\[MEDIUM\\]" "$LOG_FILE" 2>/dev/null | wc -l | xargs echo "MEDIUM severity alerts:"
grep "\\[LOW\\]" "$LOG_FILE" 2>/dev/null | wc -l | xargs echo "LOW severity alerts:"
`;

      document.getElementById('code-output-python').textContent = pythonCode;
      document.getElementById('code-output-termux').textContent = termuxCode;
      document.getElementById('code-output-windows').textContent = windowsCode;
    }

    function generateWifiScannerCode(params) {
      // Python code
      const pythonCode = `#!/usr/bin/env python3
# WiFi Scanner - Python Implementation
# Platform: Windows/Linux

import subprocess
import platform
import re

def scan_wifi_windows():
    # Scan WiFi networks on Windows
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'networks', 'mode=Bssid'],
                              capture_output=True, text=True, encoding='cp1252')

        networks = []
        current_network = {}

        for line in result.stdout.split('\\n'):
            line = line.strip()

            if line.startswith('SSID'):
                if current_network:
                    networks.append(current_network)
                ssid = line.split(':', 1)[1].strip()
                current_network = {'ssid': ssid}
            elif 'Signal' in line:
                signal = line.split(':', 1)[1].strip()
                current_network['signal'] = signal
            elif 'Authentication' in line:
                auth = line.split(':', 1)[1].strip()
                current_network['encryption'] = auth

        if current_network:
            networks.append(current_network)

        return networks
    except Exception as e:
        print(f"[!] Error: {e}")
        return []

def scan_wifi_linux():
    # Scan WiFi networks on Linux
    try:
        # Try nmcli first
        result = subprocess.run(['nmcli', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi'],
                              capture_output=True, text=True)

        networks = []
        lines = result.stdout.strip().split('\\n')[1:]  # Skip header

        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                ssid = parts[0]
                signal = parts[1]
                security = ' '.join(parts[2:]) if len(parts) > 2 else 'Open'
                networks.append({
                    'ssid': ssid,
                    'signal': signal + '%',
                    'encryption': security
                })

        return networks
    except:
        try:
            # Fallback to iwlist
            result = subprocess.run(['iwlist', 'wlan0', 'scan'],
                                  capture_output=True, text=True)
            # Parse iwlist output (simplified)
            return []
        except:
            print("[!] Error: nmcli or iwlist not available")
            return []

def main():
    print("[*] WiFi Network Scanner")
    print("-" * 60)

    system = platform.system()

    if system == 'Windows':
        print("[*] Platform: Windows")
        networks = scan_wifi_windows()
    elif system == 'Linux':
        print("[*] Platform: Linux")
        networks = scan_wifi_linux()
    else:
        print(f"[!] Unsupported platform: {system}")
        return

    if not networks:
        print("[!] No networks found")
        return

    print(f"[+] Found {len(networks)} networks:\\n")

    for i, net in enumerate(networks, 1):
        ssid = net.get('ssid', 'Hidden')
        signal = net.get('signal', 'Unknown')
        encryption = net.get('encryption', 'Unknown')

        print(f"{i}. SSID: {ssid}")
        print(f"   Signal: {signal}")
        print(f"   Security: {encryption}")
        print()

if __name__ == "__main__":
    main()
`;

      // Termux code
      const termuxCode = `#!/data/data/com.termux/files/usr/bin/bash
# WiFi Scanner - Termux/Android Implementation

echo "[*] WiFi Scanner for Android"
echo ""

# Install Termux:API if not already installed
if ! command -v termux-wifi-scaninfo &> /dev/null; then
    echo "[!] Termux:API not found"
    echo "[*] Please install 'Termux:API' app from F-Droid or Google Play"
    echo "[*] Then run: pkg install termux-api"
    exit 1
fi

echo "[*] Scanning for WiFi networks..."
echo "----------------------------------------"

# Scan using Termux API
termux-wifi-scaninfo | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)

    if not data:
        print('[!] No networks found')
        sys.exit(0)

    print(f'[+] Found {len(data)} networks:\\n')

    for i, network in enumerate(data, 1):
        ssid = network.get('ssid', 'Hidden')
        bssid = network.get('bssid', 'Unknown')
        level = network.get('rssi', 0)
        freq = network.get('frequency', 0)

        # Convert frequency to channel
        if freq >= 2412 and freq <= 2484:
            channel = (freq - 2412) // 5 + 1
            band = '2.4GHz'
        elif freq >= 5170 and freq <= 5825:
            channel = (freq - 5170) // 5 + 34
            band = '5GHz'
        else:
            channel = 0
            band = 'Unknown'

        print(f'{i}. SSID: {ssid}')
        print(f'   BSSID: {bssid}')
        print(f'   Signal: {level} dBm')
        print(f'   Channel: {channel} ({band})')
        print()

except json.JSONDecodeError:
    print('[!] Error parsing WiFi scan results')
except Exception as e:
    print(f'[!] Error: {e}')
"

echo "----------------------------------------"
echo "[*] Scan complete"
`;

      // Linux code - Show warning
      const windowsCode = `# PowerShell
# WiFi Scanner - Not recommended for standard Linux

echo "[!] WARNING: WiFi scanning on Linux requires specific tools"
echo "[!] This is better done on Windows or Android/Termux"
echo ""
echo "Available options on Linux:"
echo ""
echo "1. Using nmcli (NetworkManager):"
echo "   nmcli dev wifi list"
echo ""
echo "2. Using iwlist (requires root):"
echo "   sudo iwlist wlan0 scan"
echo ""
echo "3. Using iw (modern tool):"
echo "   sudo iw dev wlan0 scan"
echo ""

read -p "Try nmcli scan? (y/n): " choice

if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    if command -v nmcli &> /dev/null; then
        echo ""
        echo "[*] Scanning WiFi networks..."
        echo "----------------------------------------"
        nmcli -f SSID,SIGNAL,CHAN,SECURITY dev wifi list
        echo "----------------------------------------"
    else
        echo "[!] nmcli not found. Please install NetworkManager"
    fi
else
    echo "[*] Scan cancelled"
fi
`;

      document.getElementById('code-output-python').textContent = pythonCode;
      document.getElementById('code-output-termux').textContent = termuxCode;
      document.getElementById('code-output-windows').textContent = windowsCode;

      // Show warning for Linux
      document.getElementById('code-warning-windows').textContent ='⚠ WiFi scanning not recommended on Linux - use Windows or Android/Termux instead';
      document.getElementById('code-warning-windows').style.display ='block';
    }

    // Tool Output Modal
    let currentToolData = null;
    let currentToolName = null;
    
    function showToolModal(toolName, toolData) {
      currentToolName = toolName;
      currentToolData = toolData;
      document.getElementById('tool-modal-title').textContent = toolName.toUpperCase().replace('_', ' ');
      document.getElementById('tool-output-modal').classList.add('active');
      switchToolTab('output');
      updateToolCode();
    }
    
    function closeToolModal() {
      document.getElementById('tool-output-modal').classList.remove('active');
      currentToolData = null;
      currentToolName = null;
    }
    
    function switchToolTab(tab) {
      // Update tab buttons
      const tabs = document.querySelectorAll('.tool-modal-tab');
      tabs.forEach(btn => btn.classList.remove('active'));
      
      // Update panels
      document.getElementById('tool-output-panel').classList.remove('active');
      document.getElementById('tool-code-panel').classList.remove('active');
      
      if (tab === 'output') {
        document.getElementById('tool-output-panel').classList.add('active');
        tabs[0].classList.add('active');
      } else {
        document.getElementById('tool-code-panel').classList.add('active');
        tabs[1].classList.add('active');
        updateToolCode();
      }
    }
    
    function updateToolCode() {
      if (!currentToolData || !currentToolName) {
        document.getElementById('tool-code-output').textContent = 'No tool data available';
        return;
      }
      
      const lang = document.getElementById('tool-code-language').value;
      let code = '';
      
      // Generate code based on tool and language
      if (currentToolName === 'port_scanner') {
        const host = currentToolData.host || '127.0.0.1';
        const ports = currentToolData.ports || [];
        const startPort = currentToolData.start_port;
        const endPort = currentToolData.end_port;
        
        if (lang === 'python') {
          if (startPort && endPort) {
            code = `from security_tools import PortScanner\n\nresult = PortScanner.scan_range('${host}', ${startPort}, ${endPort}, timeout=1.0)\nprint(result)`;
          } else if (ports.length > 0) {
            code = `from security_tools import PortScanner\n\nports = [${ports.join(', ')}]\nresult = PortScanner.scan_host('${host}', ports, timeout=1.0)\nprint(result)`;
          } else {
            code = `from security_tools import PortScanner\n\ncommon_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080]\nresult = PortScanner.scan_host('${host}', common_ports, timeout=1.0)\nprint(result)`;
          }
        } else if (lang === 'bash') {
          if (startPort && endPort) {
            code = `#!/bin/bash\nhost="${host}"\nfor port in $(seq ${startPort} ${endPort}); do\n  timeout 1 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null && echo "Port $port is open"\ndone`;
          } else if (ports.length > 0) {
            code = `#!/bin/bash\nhost="${host}"\nports=(${ports.join(' ')})\nfor port in "${ports.join('" "')}"; do\n  timeout 1 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null && echo "Port $port is open"\ndone`;
          } else {
            code = `#!/bin/bash\nhost="${host}"\nports=(21 22 23 25 53 80 110 143 443 445 3306 3389 5432 8080)\nfor port in "${ports.join('" "')}"; do\n  timeout 1 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null && echo "Port $port is open"\ndone`;
          }
        } else { // termux
          if (startPort && endPort) {
            code = `pkg install nmap -y\nnmap -p ${startPort}-${endPort} ${host}`;
          } else if (ports.length > 0) {
            code = `pkg install nmap -y\nnmap -p ${ports.join(',')} ${host}`;
          } else {
            code = `pkg install nmap -y\nnmap -F ${host}`;
          }
        }
      } else if (currentToolName === 'packet_sniffer') {
        const interface = currentToolData.interface || 'eth0';
        const count = currentToolData.count || 100;
        if (lang === 'python') {
          code = `from security_tools import PacketSniffer\n\nsniffer = PacketSniffer()\nsniffer.start_sniff(interface='${interface}', count=${count})\npackets = sniffer.get_packets()\nprint(packets)`;
        } else if (lang === 'bash') {
          code = `#!/bin/bash\nsudo tcpdump -i ${interface} -c ${count} -n`;
        } else { // termux
          code = `pkg install tcpdump -y\ntcpdump -i any -c ${count} -n`;
        }
      } else if (currentToolName === 'remote_shell') {
        const host = currentToolData.host || 'localhost';
        const command = currentToolData.command || 'whoami';
        if (lang === 'python') {
          code = `from security_tools import RemoteShell\n\nshell = RemoteShell()\nresult = shell.execute_ssh('${host}', '${command}')\nprint(result)`;
        } else if (lang === 'bash') {
          code = `#!/bin/bash\nssh ${host} "${command}"`;
        } else { // termux
          code = `pkg install openssh -y\nssh ${host} "${command}"`;
        }
      } else if (currentToolName === 'threat_monitor') {
        if (lang === 'python') {
          code = `from security_tools import ThreatMonitor\n\nmonitor = ThreatMonitor()\nmonitor.start_monitor()\nthreats = monitor.get_threats()\nprint(threats)`;
        } else if (lang === 'bash') {
          code = `#!/bin/bash\nwhile true; do\n  netstat -an | grep ESTABLISHED\n  sleep 5\ndone`;
        } else { // termux
          code = `pkg install net-tools -y\nwhile true; do\n  netstat -an | grep ESTABLISHED\n  sleep 5\ndone`;
        }
      } else if (currentToolName === 'vuln_scanner') {
        const host = currentToolData.host || '127.0.0.1';
        if (lang === 'python') {
          code = `from security_tools import VulnScanner\n\nscanner = VulnScanner()\nresult = scanner.scan_host('${host}')\nprint(result)`;
        } else if (lang === 'bash') {
          code = `#!/bin/bash\nnmap --script vuln ${host}`;
        } else { // termux
          code = `pkg install nmap -y\nnmap --script vuln ${host}`;
        }
      } else if (currentToolName === 'log_analyzer') {
        const logFile = currentToolData.log_file || '/var/log/syslog';
        const patterns = currentToolData.patterns || ['ERROR', 'WARNING'];
        if (lang === 'python') {
          code = `from security_tools import LogAnalyzer\n\nanalyzer = LogAnalyzer()\nresult = analyzer.analyze_log('${logFile}', ${JSON.stringify(patterns)})\nprint(result)`;
        } else if (lang === 'bash') {
          code = `#!/bin/bash\ngrep -E "${patterns.join('|')}" ${logFile}`;
        } else { // termux
          code = `grep -E "${patterns.join('|')}" ${logFile}`;
        }
      } else {
        code = `# Code generation for ${currentToolName} not yet implemented`;
      }
      
      document.getElementById('tool-code-output').textContent = code;
    }
    
    function appendToolOutput(text) {
      const output = document.getElementById('tool-result-output');
      output.textContent += text + '\\n';
      output.scrollTop = output.scrollHeight;
    }
    
    function setToolOutput(text) {
      document.getElementById('tool-result-output').textContent = text;
    }
    
    // Authentication
    function authenticate() {
      const key = prompt("Enter authentication key:");
      if (!key) return;
      
      fetch('/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({key})
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'authenticated') {
          authenticated = true;
          document.getElementById('auth-btn').classList.add('active');
          log("Authentication successful");
          showNotification("Authentication successful");
        } else {
          showNotification("Authentication failed: " + data.message);
        }
      })
      .catch(error => {
        showNotification("Authentication error");
      });
    }
    
    // WiFi Cracker
    function crackWifi() {
      // DEVELOPER MODE: Authentication bypassed for KingKali
      // if (!authenticated) {
      //   showNotification("Please authenticate first");
      //   return;
      // }
      
      const panel = document.getElementById('wifi-panel');
      const progress = document.getElementById('wifi-progress');
      panel.style.display = 'block';
      progress.innerHTML = '<div style="font-size:32px;margin-bottom:20px;animation:blink 1s infinite">[SCANNING]</div>';
      
      fetch('/wifi/scan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      })
      .then(response => response.json())
      .then(data => {
        if (data.networks && data.networks.length > 0) {
          showWifiCrackSequence(data.networks, progress);
        } else {
          showWifiCrackSequence([], progress);
        }
      })
      .catch(error => {
        showWifiCrackSequence([], progress);
      });
    }
    
    function showWifiCrackSequence(networks, progressEl) {
      let step = 0;
      const maxNetworks = 8;
      
      const targetNetworks = networks.length > 0 ? networks.slice(0, maxNetworks) : [
        {ssid: 'Linksys_5G', signal: -45, encryption: 'WPA2'},
        {ssid: 'NETGEAR_Home', signal: -52, encryption: 'WPA2'},
        {ssid: 'TP-Link_Router', signal: -58, encryption: 'WPA3'},
        {ssid: 'HomeSweetHome', signal: -61, encryption: 'WPA2'},
        {ssid: 'Public_WiFi', signal: -67, encryption: 'OPEN'},
        {ssid: 'Family_WiFi', signal: -71, encryption: 'WPA2'},
        {ssid: 'Guest_Network', signal: -75, encryption: 'WPA2'},
        {ssid: 'Office_2024', signal: -78, encryption: 'WPA2'}
      ];
      
      function nextStep() {
        if (step < targetNetworks.length) {
          const net = targetNetworks[step];
          const percent = ((step + 1) / targetNetworks.length * 100).toFixed(0);
          
          progressEl.innerHTML = `
            <div style="color:#0f0;font-size:14px;margin-bottom:10px">[${step + 1}/${targetNetworks.length}] Scanning...</div>
            <div style="font-size:20px;margin-bottom:15px;color:#f33">FOUND: ${net.ssid}</div>
            <div style="font-size:12px;color:#888;margin-bottom:20px">Signal: ${net.signal}dBm | ${net.encryption}</div>
            <div style="width:100%;height:20px;border:1px solid #f33;background:#000"><div style="width:${percent}%;height:100%;background:#f33;transition:width 0.3s"></div></div>
          `;
          step++;
          setTimeout(nextStep, 800);
        } else if (step === targetNetworks.length) {
          crackSequence(progressEl);
        }
      }
      
      setTimeout(nextStep, 1000);
    }
    
    function crackSequence(progressEl) {
      progressEl.innerHTML = '<div style="font-size:32px;margin-bottom:20px;color:#f33;animation:blink 0.5s infinite">[CRACKING]</div>';
      
      const passwords = ['password123', 'admin123', 'qwerty123', 'welcome2024', 'letmein', '12345678', 'password', 'admin'];
      let passIdx = 0;
      const targetPass = passwords[Math.floor(Math.random() * passwords.length)];
      
      function tryPassword() {
        if (passIdx < passwords.length) {
          const pass = passwords[passIdx];
          const isCorrect = pass === targetPass;
          
          progressEl.innerHTML = `
            <div style="font-size:18px;margin-bottom:15px;color:#f33">TRYING: ${pass}</div>
            <div style="font-size:14px;color:${isCorrect ? '#0f0' : '#888'};margin-bottom:10px">${isCorrect ? '✓ MATCH!' : '✗ NO MATCH'}</div>
            <div style="font-size:12px;color:#888">Attempt ${passIdx + 1}/${passwords.length}</div>
          `;
          
          passIdx++;
          
          if (isCorrect) {
            setTimeout(() => showSuccess(progressEl, pass), 1000);
          } else {
            setTimeout(tryPassword, 600);
          }
        } else {
          setTimeout(() => showSuccess(progressEl, targetPass), 800);
        }
      }
      
      setTimeout(tryPassword, 800);
    }
    
    function showSuccess(progressEl, password) {
      progressEl.innerHTML = `
        <div style="font-size:48px;color:#0f0;text-shadow:0 0 20px #0f0;margin-bottom:20px;animation:blink 0.3s infinite">ACCESS GRANTED</div>
        <div style="font-size:24px;color:#f33;margin-bottom:15px">PASSWORD: ${password}</div>
        <div style="font-size:16px;color:#0f0">✓ Network connected</div>
        <div style="font-size:14px;color:#888;margin-top:10px">Full access achieved</div>
      `;
      
      // Add CSS animation if not exists
      if (!document.getElementById('wifi-blink-style')) {
        const style = document.createElement('style');
        style.id = 'wifi-blink-style';
        style.textContent = '@keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0.3 } }';
        document.head.appendChild(style);
      }
      
      log("WiFi cracked: " + password);
    }
    
    // Control - PHASE 2: Enhanced with 3 button states
    function takeControl() {
      // DEVELOPER MODE: Authentication bypassed for KingKali
      // if (!authenticated) {
      //   showNotification("Please authenticate first");
      //   return;
      // }

      const btn = document.getElementById('control-btn');

      // Check current state - if peer-control (grayed), don't allow taking control
      if (btn.classList.contains('peer-control')) {
        showNotification("Another device has control");
        return;
      }

      const willHaveAuthority = !btn.classList.contains('master-control');

      console.log('[AUTHORITY] takeControl called:', {
        willHaveAuthority: willHaveAuthority,
        currentClasses: btn.className
      });

      log(`[AUTHORITY] Attempting to ${willHaveAuthority ? 'take' : 'release'} control...`);

      // INSTANT UI feedback - optimistic update
      updateControlButton(willHaveAuthority, 'local_device', null);

      fetch('/sync/authority', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          device_id: 'local_device',
          has_authority: willHaveAuthority,
          timestamp: Date.now() / 1000  // PHASE 2: Send timestamp for conflict resolution
        })
      })
      .then(response => {
        console.log('[AUTHORITY] Authority response status:', response.status);
        return response.json();
      })
      .then(data => {
        console.log('[AUTHORITY] Authority response data:', data);

        // Handle conflict
        if (data.status === 'authority_conflict') {
          const masterName = data.current_authority_name || data.current_authority;
          log(`Control denied: ${masterName} has control`);
          showNotification(`Control denied: ${masterName} has control`);
          // Update button to show peer state
          updateControlButton(false, data.current_authority, masterName);
        } else {
          const message = willHaveAuthority ? "Control assumed" : "Control released";
          log(message);
          log(`[AUTHORITY] Authority status: ${JSON.stringify(data)}`);
          showNotification(willHaveAuthority ? "Control activated" : "Control deactivated");
          // Update button with final state
          updateControlButton(data.has_authority, data.current_authority, data.current_authority_name);
        }

        // Force status update to refresh role display and sync with other peers
        setTimeout(updateStatus, 100);
      })
      .catch(error => {
        console.error('[AUTHORITY] Control error:', error);
        log(`[AUTHORITY] Control error: ${error}`);
        showNotification("Control error: " + error);
        // Revert UI on error
        updateControlButton(false, null, null);
      });
    }

    // PHASE 2: Update control button state - 3 states: IDLE, MASTER, PEER
    function updateControlButton(hasMaster, masterDeviceId, masterName) {
      const btn = document.getElementById('control-btn');
      const isLocalMaster = hasMaster && (masterDeviceId === 'local_device' || !masterDeviceId);

      // Remove all state classes
      btn.classList.remove('idle-control', 'master-control', 'peer-control', 'red', 'active');

      if (isLocalMaster) {
        // STATE 1: MASTER - This device has control
        btn.classList.add('master-control');
        btn.textContent = 'YOU HAVE CONTROL';
        btn.disabled = false;
        console.log('[AUTHORITY] Button state: MASTER');
      } else if (masterDeviceId && !isLocalMaster) {
        // STATE 2: PEER - Another device has control
        btn.classList.add('peer-control');
        btn.textContent = 'MASTER: ' + (masterName || masterDeviceId);
        btn.disabled = false;  // Allow clicking to show notification
        console.log('[AUTHORITY] Button state: PEER (master: ' + masterName + ')');
      } else {
        // STATE 3: IDLE - No one has control
        btn.classList.add('idle-control', 'red');
        btn.textContent = 'TAKE CONTROL';
        btn.disabled = false;
        console.log('[AUTHORITY] Button state: IDLE');
      }
    }

    // Sync
    function syncAll() {
      fetch('/sync/all', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
      })
      .then(response => response.json())
      .then(data => {
        lastSync = Date.now();
        log("Sync triggered");
        showNotification("Sync complete");
        updateStatus();
      })
      .catch(error => {
        showNotification("Sync error");
      });
    }
    
    // History
    function showHistory() {
      fetch('/status')
      .then(response => response.json())
      .then(data => {
        log("=== Command History ===");
        if (data.commands && data.commands.length > 0) {
          data.commands.forEach(cmd => {
            log(`${cmd.type} from ${cmd.source} at ${new Date(cmd.timestamp * 1000).toLocaleTimeString()}`);
          });
        } else {
          log("No commands in history");
        }
      })
      .catch(error => {
        showNotification("History error");
      });
    }
    
    // Tools - REAL IMPLEMENTATIONS
        function activateTool(tool) {
      // REMOVED AUTH CHECK - Tools run immediately!
      currentTool = tool;

      // Route to specific tool handler - ACTUALLY EXECUTE THE TOOLS
      if (tool === 'port_scanner') {
        runPortScanner();
      } else if (tool === 'packet_sniffer') {
        runPacketSniffer();
      } else if (tool === 'file_transfer') {
        sendFile();  // Already implemented
      } else if (tool === 'remote_shell') {
        runRemoteShell();
      } else if (tool === 'exploit_launcher') {
        runExploitLauncher();
      } else if (tool === 'threat_monitor') {
        runThreatMonitor();
      } else if (tool === 'vuln_scanner') {
        runVulnScanner();
      } else if (tool === 'log_analyzer') {
        runLogAnalyzer();
      } else {
        // Fallback to old method
        fetch('/sync/tool', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({tool})
        })
        .then(response => response.json())
        .then(data => {
          log(`Tool activated: ${tool}`);
          showNotification(`Tool: ${tool} activated`);
        })
        .catch(error => {
          showNotification("Tool activation error");
        });
      }
    }
    
    // Port Scanner
    function runPortScanner() {
      const host = prompt("Enter host to scan (e.g., 127.0.0.1 or scanme.nmap.org):", "127.0.0.1");
      if (!host) return;
      
      const portInput = prompt("Enter ports (e.g., 80,443 or 1-1000 or leave blank for common ports):", "");
      let ports = null;
      let startPort = null;
      let endPort = null;
      
      if (portInput) {
        if (portInput.includes('-')) {
          const parts = portInput.split('-');
          startPort = parseInt(parts[0]);
          endPort = parseInt(parts[1]);
        } else {
          ports = portInput.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p));
        }
      }
      
      // Store tool data for code generation
      const toolData = {host, ports, start_port: startPort, end_port: endPort};
      showToolModal('port_scanner', toolData);
      setToolOutput(`Starting port scan on ${host}...\\n`);
      
      log(`Starting port scan on ${host}...`);
      showNotification("Port scan started...");
      
      fetch('/tools/port_scanner/scan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({host, ports, start_port: startPort, end_port: endPort})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok' && data.result) {
          const result = data.result;
          let output = `=== Port Scan Results: ${result.host} ===\\n`;
          output += `Host: ${result.host}\\n`;
          output += `Open ports: ${result.open_ports.length > 0 ? result.open_ports.join(', ') : 'None'}\\n`;
          output += `Closed ports: ${result.closed_ports ? result.closed_ports.length : 0}\\n\\n`;
          
          if (result.services && Object.keys(result.services).length > 0) {
            output += "Services detected:\\n";
            Object.keys(result.services).forEach(port => {
              const svc = result.services[port];
              output += `  Port ${port}: ${svc.service} ${svc.version ? '(' + svc.version + ')' : ''} ${svc.product ? '- ' + svc.product : ''}\\n`;
            });
            output += "\\n";
          }
          
          if (result.errors && result.errors.length > 0) {
            output += "Errors:\\n";
            result.errors.forEach(err => {
              output += `  ${err}\\n`;
            });
          }
          
          setToolOutput(output);
          log(`Port scan complete: ${result.open_ports.length} open ports found`);
          showNotification(`Scan complete: ${result.open_ports.length} open ports found`);
        } else {
          const errorMsg = "Port scan error: " + (data.error || 'Unknown error');
          setToolOutput(errorMsg);
          log(errorMsg);
          showNotification("Port scan failed");
        }
      })
      .catch(err => {
        const errorMsg = "Port scan error: " + err;
        setToolOutput(errorMsg);
        log(errorMsg);
        showNotification("Port scan error");
      });
    }
    
    // Packet Sniffer
    let packetSnifferRunning = false;
    function runPacketSniffer() {
      if (packetSnifferRunning) {
        // Stop sniffing
        fetch('/tools/packet_sniffer/stop', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({})
        })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'ok') {
            packetSnifferRunning = false;
            log("Packet sniffer stopped. Packets captured: " + (data.result?.packets_captured || 0));
            showNotification("Packet sniffer stopped");
          }
        });
        return;
      }
      
      const count = prompt("Number of packets to capture (default 100):", "100");
      const filter = prompt("BPF filter (leave blank for all packets):", "");
      
      log("Starting packet capture...");
      showNotification("Packet sniffer started...");
      
      fetch('/tools/packet_sniffer/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({count: parseInt(count) || 100, filter: filter || ''})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          packetSnifferRunning = true;
          log("Packet sniffer started. Capturing packets...");
          
          // Poll for packets
          const pollInterval = setInterval(() => {
            fetch('/tools/packet_sniffer/packets', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({})
            })
            .then(r => r.json())
            .then(packetData => {
              if (packetData.status === 'ok' && packetData.result) {
                const result = packetData.result;
                if (!result.sniffing && result.packets) {
                  clearInterval(pollInterval);
                  packetSnifferRunning = false;
                  log(`\\n=== Packet Sniffer Results ===`);
                  log(`Packets captured: ${result.count}`);
                  result.packets.slice(-20).forEach((pkt, idx) => {
                    if (pkt.error) {
                      log(`Error: ${pkt.error}`);
                    } else {
                      log(`${idx + 1}. ${pkt.summary || 'Packet'}`);
                      if (pkt.src && pkt.dst) log(`   ${pkt.src} -> ${pkt.dst} (${pkt.protocol})`);
                    }
                  });
                  showNotification(`Captured ${result.count} packets`);
                }
              }
            });
          }, 1000);
        } else {
          log("Packet sniffer error: " + (data.error || data.result?.error || 'Unknown error'));
          showNotification("Packet sniffer failed");
        }
      })
      .catch(err => {
        log("Packet sniffer error: " + err);
        showNotification("Packet sniffer error");
      });
    }
    
    // Remote Shell
    function runRemoteShell() {
      const useSSH = confirm("Use SSH? (Cancel for local command)");
      
      if (useSSH) {
        const host = prompt("SSH Host:", "");
        if (!host) return;
        const username = prompt("Username:", "");
        if (!username) return;
        const password = prompt("Password:", "");
        const command = prompt("Command to execute:", "");
        if (!command) return;
        
        log(`Executing SSH command on ${host}...`);
        
        fetch('/tools/remote_shell/execute', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({host, username, password, command})
        })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'ok' && data.result) {
            const result = data.result;
            if (result.error) {
              log("SSH Error: " + result.error);
            } else {
              log(`\\n=== SSH Command Output ===`);
              if (result.stdout) log(result.stdout);
              if (result.stderr) log("STDERR: " + result.stderr);
              log(`Exit status: ${result.exit_status}`);
            }
          } else {
            log("Remote shell error: " + (data.error || 'Unknown error'));
          }
        });
      } else {
        const command = prompt("Command to execute:", "");
        if (!command) return;
        
        log(`Executing local command...`);
        
        fetch('/tools/remote_shell/execute', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({command})
        })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'ok' && data.result) {
            const result = data.result;
            if (result.error) {
              log("Command Error: " + result.error);
            } else {
              log(`\\n=== Command Output ===`);
              if (result.stdout) log(result.stdout);
              if (result.stderr) log("STDERR: " + result.stderr);
              log(`Exit status: ${result.exit_status}`);
            }
          } else {
            log("Command error: " + (data.error || 'Unknown error'));
          }
        });
      }
    }
    
    // Exploit Launcher
    function runExploitLauncher() {
      const payloadType = prompt("Payload type (command/script/metasploit):", "command");
      if (!payloadType) return;
      
      const target = prompt("Target (hostname/IP):", "localhost");
      if (!target) return;
      
      let payloadData = {};
      
      if (payloadType === 'command') {
        const command = prompt("Command to execute:", "");
        if (!command) return;
        payloadData = {command};
      } else if (payloadType === 'script') {
        const script = prompt("Script content:", "");
        if (!script) return;
        const lang = prompt("Language (python/bash):", "python");
        payloadData = {script, language: lang};
      } else if (payloadType === 'metasploit') {
        const msfCmd = prompt("Metasploit command:", "");
        if (!msfCmd) return;
        payloadData = {msf_command: msfCmd};
      }
      
      log(`Launching ${payloadType} payload on ${target}...`);
      
      fetch('/tools/exploit_launcher/launch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({payload_type: payloadType, target, payload_data: payloadData})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok' && data.result) {
          const result = data.result;
          if (result.error) {
            log("Exploit Error: " + result.error);
          } else {
            log(`\\n=== Exploit Launcher Output ===`);
            log(`Type: ${result.type}`);
            if (result.result) {
              if (result.result.stdout) log(result.result.stdout);
              if (result.result.stderr) log("STDERR: " + result.result.stderr);
            } else {
              log("Status: " + (result.status || 'executed'));
            }
          }
        } else {
          log("Exploit launcher error: " + (data.error || 'Unknown error'));
        }
      });
    }
    
    // Threat Monitor
    let threatMonitorRunning = false;
    function runThreatMonitor() {
      if (threatMonitorRunning) {
        // Stop monitoring
        fetch('/tools/threat_monitor/stop', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({})
        })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'ok') {
            threatMonitorRunning = false;
            log("Threat monitor stopped. Threats found: " + (data.result?.threats_found || 0));
            showNotification("Threat monitor stopped");
          }
        });
        return;
      }
      
      log("Starting threat monitor...");
      showNotification("Threat monitor started...");
      
      fetch('/tools/threat_monitor/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          threatMonitorRunning = true;
          log("Threat monitor started. Monitoring for threats...");
          
          // Poll for threats
          const pollInterval = setInterval(() => {
            if (!threatMonitorRunning) {
              clearInterval(pollInterval);
              return;
            }
            
            fetch('/tools/threat_monitor/threats', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({})
            })
            .then(r => r.json())
            .then(threatData => {
              if (threatData.status === 'ok' && threatData.result) {
                const result = threatData.result;
                if (result.threats && result.threats.length > 0) {
                  log(`\\n=== Threat Monitor: ${result.count} threats detected ===`);
                  result.threats.slice(-10).forEach((threat, idx) => {
                    log(`${idx + 1}. [${threat.severity?.toUpperCase() || 'UNKNOWN'}] ${threat.type || 'threat'}: ${threat.message || threat.details || 'N/A'}`);
                  });
                }
              }
            });
          }, 5000);  // Check every 5 seconds
        } else {
          log("Threat monitor error: " + (data.error || 'Unknown error'));
          showNotification("Threat monitor failed");
        }
      })
      .catch(err => {
        log("Threat monitor error: " + err);
        showNotification("Threat monitor error");
      });
    }
    
    // Vulnerability Scanner
    function runVulnScanner() {
      const host = prompt("Enter host to scan:", "127.0.0.1");
      if (!host) return;
      
      log(`Starting vulnerability scan on ${host}...`);
      showNotification("Vulnerability scan started...");
      
      fetch('/tools/vuln_scanner/scan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({host})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok' && data.result) {
          const result = data.result;
          log(`\\n=== Vulnerability Scan Results: ${result.host} ===`);
          log(`Open ports: ${result.open_ports.join(', ') || 'None'}`);
          
          if (result.vulnerabilities && result.vulnerabilities.length > 0) {
            log(`\\nVulnerabilities found: ${result.vulnerabilities.length}`);
            result.vulnerabilities.forEach((vuln, idx) => {
              log(`\\n${idx + 1}. [${vuln.severity.toUpperCase()}] ${vuln.service} (Port ${vuln.port})`);
              log(`   Issue: ${vuln.issue}`);
              log(`   Recommendation: ${vuln.recommendation}`);
            });
          } else {
            log("No known vulnerabilities detected");
          }
          
          showNotification(`Scan complete: ${result.vulnerabilities?.length || 0} vulnerabilities found`);
        } else {
          log("Vulnerability scan error: " + (data.error || 'Unknown error'));
          showNotification("Vulnerability scan failed");
        }
      })
      .catch(err => {
        log("Vulnerability scan error: " + err);
        showNotification("Vulnerability scan error");
      });
    }
    
    // Log Analyzer
    function runLogAnalyzer() {
      const logFile = prompt("Enter log file path:", "/var/log/auth.log");
      if (!logFile) return;
      
      log(`Analyzing log file: ${logFile}...`);
      showNotification("Log analysis started...");
      
      fetch('/tools/log_analyzer/analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({log_file: logFile})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok' && data.result) {
          const result = data.result;
          if (result.error) {
            log("Log analyzer error: " + result.error);
          } else {
            log(`\\n=== Log Analysis Results: ${result.log_file} ===`);
            log(`Total lines: ${result.total_lines}`);
            
            if (result.pattern_count) {
              log(`\\nPattern matches:`);
              Object.keys(result.pattern_count).forEach(pattern => {
                const count = result.pattern_count[pattern];
                if (count > 0) {
                  log(`  ${pattern}: ${count} matches`);
                  if (result.matches && result.matches[pattern]) {
                    result.matches[pattern].slice(-5).forEach(match => {
                      log(`    Line ${match.line}: ${match.content.substring(0, 80)}...`);
                    });
                  }
                }
              });
            }
            
            showNotification("Log analysis complete");
          }
        } else {
          log("Log analyzer error: " + (data.error || 'Unknown error'));
          showNotification("Log analysis failed");
        }
      })
      .catch(err => {
        log("Log analyzer error: " + err);
        showNotification("Log analysis error");
      });
    }

    // Plugins
    function startTunnel() {
      // DEVELOPER MODE: Authentication bypassed for KingKali
      // if (!authenticated) { showNotification('Please authenticate first'); return; }
      
      console.log('[DEBUG] startTunnel called');
      log('[DEBUG] Starting tunnel...');
      
      fetch('/plugins/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: 'tunnel'})
      })
      .then(r => {
        console.log('[DEBUG] Tunnel start response status:', r.status);
        return r.json();
      })
      .then(d => {
        console.log('[DEBUG] Tunnel start response:', d);
        if (d.status === 'ok') {
          const message = d.result?.message || 'Tunnel starting';
          log('Tunnel start: ' + message);
          showNotification(message);
          
          // Show wireguard status if available
          if (d.result?.wireguard !== undefined) {
            log('WireGuard: ' + (d.result.wireguard ? 'ENABLED' : 'BASIC MODE'));
          }
          
          // Update UI immediately
          setTimeout(updateStatus, 500);
        } else {
          const errorMsg = d.result?.message || 'Unknown error';
          const details = d.result?.details || [];
          log('Tunnel start FAILED: ' + errorMsg);
          if (details.length > 0) {
            log('Error details:');
            details.forEach((detail, idx) => {
              log(`  ${idx + 1}. ${detail}`);
            });
          }
          showNotification('Tunnel start failed: ' + errorMsg);
          console.error('[DEBUG] Tunnel start error details:', d);
        }
      })
      .catch((err) => {
        console.error('[DEBUG] Tunnel start exception:', err);
        log('Tunnel start ERROR: ' + err);
        showNotification('Tunnel start error: ' + err);
      });
    }

    // File transfer
    let selectedFilePath = null;
    let activeTransferId = null;
    
    function sendFile() {
      const panel = document.getElementById('file-transfer-panel');
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      
      if (panel.style.display === 'block') {
        updateNodeList();
      }
    }
    
    function updateNodeList() {
      fetch('/status')
        .then(r => r.json())
        .then(data => {
          const select = document.getElementById('target-node-select');
          select.innerHTML = '<option value="">Select target node...</option>';
          
          // Get all available nodes - include master and peers
          const nodes = data.nodes || {};
          const currentDeviceId = data.device_id || '';
          
          // Add master node if we're a peer (or vice versa)
          // If we're master, show all peers. If peer, show master + other peers
          const isMaster = data.is_master === true || data.mode === 'master';
          
          if (!isMaster && data.master_device_id) {
            // We're a peer - add master to list
            const masterOption = document.createElement('option');
            masterOption.value = data.master_device_id;
            masterOption.textContent = `${data.master_device_id} (master)`;
            select.appendChild(masterOption);
          }
          
          // Add all peer nodes (exclude self)
          if (nodes) {
            Object.keys(nodes).forEach(nodeId => {
              if (nodeId !== currentDeviceId) {  // Don't show self
                const node = nodes[nodeId];
                const option = document.createElement('option');
                option.value = nodeId;
                option.textContent = `${nodeId} (${node.platform || 'peer'})`;
                select.appendChild(option);
              }
            });
          }
          
          // If no nodes available, show message
          if (select.options.length === 1) {
            const noNodeOption = document.createElement('option');
            noNodeOption.value = '';
            noNodeOption.textContent = 'No other nodes available';
            noNodeOption.disabled = true;
            select.appendChild(noNodeOption);
          }
        })
        .catch(err => {
          console.error('Error updating node list:', err);
          const select = document.getElementById('target-node-select');
          select.innerHTML = '<option value="">Error loading nodes</option>';
        });
    }
    
    function handleFileSelect(event) {
      const file = event.target.files[0];
      if (!file) return;
      
      // Read file as base64
      const reader = new FileReader();
      reader.onload = function(e) {
        const base64Data = e.target.result.split(',')[1]; // Remove data:... prefix
        selectedFilePath = {
          name: file.name,
          size: file.size,
          data: base64Data,
          type: file.type
        };
        document.getElementById('selected-file').textContent = file.name + ' (' + formatFileSize(file.size) + ')';
        document.getElementById('send-file-btn-transfer').style.display = 'inline-block';
        
        // Auto-start transfer if target selected
        const targetNode = document.getElementById('target-node-select').value;
        if (targetNode && selectedFilePath) {
          // Don't auto-start, let user click Send
        }
      };
      reader.readAsDataURL(file);
    }
    
    function formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    function startFileTransfer() {
      const targetNode = document.getElementById('target-node-select').value;
      if (!targetNode) {
        showNotification('Please select a target node');
        return;
      }
      if (!selectedFilePath) {
        showNotification('Please select a file first');
        return;
      }
      
      fetch('/file/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          file_name: selectedFilePath.name,
          file_data: selectedFilePath.data,
          file_size: selectedFilePath.size,
          target_node: targetNode
        })
      })
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          activeTransferId = data.transfer_id;
          document.getElementById('transfer-progress-container').style.display = 'block';
          showNotification('File transfer started: ' + data.file_name);
          monitorTransfer(data.transfer_id);
        } else {
          showNotification('Transfer failed: ' + data.message);
        }
      })
      .catch(err => {
        showNotification('Transfer error: ' + err);
      });
    }
    
    function monitorTransfer(transferId) {
      const interval = setInterval(() => {
        fetch(`/file/transfer/${transferId}`)
          .then(r => r.json())
          .then(data => {
            if (data.status) {
              const progress = data.progress || 0;
              document.getElementById('transfer-progress').style.width = progress + '%';
              document.getElementById('transfer-status').textContent = 
                `${data.file_name || ''} - ${progress.toFixed(1)}% - ${data.status}`;
              
              if (data.status === 'completed') {
                clearInterval(interval);
                showNotification('File transfer completed: ' + data.file_name);
                setTimeout(() => {
                  document.getElementById('transfer-progress-container').style.display = 'none';
                  selectedFilePath = null;
                  document.getElementById('selected-file').textContent = '';
                }, 3000);
              } else if (data.status === 'error') {
                clearInterval(interval);
                showNotification('Transfer error: ' + (data.error || 'Unknown error'));
              }
            }
          })
          .catch(err => {
            clearInterval(interval);
            showNotification('Monitor error: ' + err);
          });
      }, 500);
    }

    function stopTunnel() {
      // DEVELOPER MODE: Authentication bypassed for KingKali
      // if (!authenticated) { showNotification('Please authenticate first'); return; }
      
      console.log('[DEBUG] stopTunnel called');
      log('[DEBUG] Stopping tunnel...');
      
      fetch('/plugins/stop', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: 'tunnel'})
      })
      .then(r => {
        console.log('[DEBUG] Tunnel stop response status:', r.status);
        return r.json();
      })
      .then(d => {
        console.log('[DEBUG] Tunnel stop response:', d);
        if (d.status === 'ok') {
          const message = d.result?.message || 'Tunnel stopping';
          log('Tunnel stop: ' + message);
          showNotification(message);
          
          // Show warnings if any
          if (d.result?.warnings && d.result.warnings.length > 0) {
            log('Warnings:');
            d.result.warnings.forEach((warn, idx) => {
              log(`  ${idx + 1}. ${warn}`);
            });
          }
          
          // Update UI immediately
          setTimeout(updateStatus, 500);
        } else {
          const errorMsg = d.result?.message || 'Unknown error';
          const details = d.result?.details || [];
          log('Tunnel stop FAILED: ' + errorMsg);
          if (details.length > 0) {
            log('Error details:');
            details.forEach((detail, idx) => {
              log(`  ${idx + 1}. ${detail}`);
            });
          }
          showNotification('Tunnel stop failed: ' + errorMsg);
          console.error('[DEBUG] Tunnel stop error details:', d);
        }
      })
      .catch((err) => {
        console.error('[DEBUG] Tunnel stop exception:', err);
        log('Tunnel stop ERROR: ' + err);
        showNotification('Tunnel stop error: ' + err);
      });
    }

    function showPlugins() {
      fetch('/plugins/status')
      .then(r => r.json())
      .then(d => {
        const plugins = d.plugins || {};
        const names = Object.keys(plugins);
        log('Plugins: ' + (names.length ? names.join(', ') : 'none'));
        names.forEach(n => {
          try { log(n + ': ' + JSON.stringify(plugins[n])); } catch (_) {}
        });
        showNotification('Plugin status fetched');
      })
      .catch(() => showNotification('Plugin status error'));
    }
    
    // Update UI
    // PAGE SWITCHING
    let currentPage = 0;  // Start at main menu
    function showPage(pageNum) {
      currentPage = pageNum;
      
      // Hide all pages
      for (let i = 0; i <= 4; i++) {
        const page = document.getElementById(`page-${i}`);
        if (page) page.style.display = 'none';
      }
      
      // Show selected page
      const selectedPage = document.getElementById(`page-${pageNum}`);
      if (selectedPage) selectedPage.style.display = 'block';
      
      // Initialize control room if showing page 3
      if (pageNum === 3) {
        setTimeout(() => {
          try {
            initNetworkMap();
            initRadar();
            initHouseRenderer();
            console.log('[Control Room] Initialized all systems');
          } catch (e) {
            console.error('[Control Room] Initialization error:', e);
          }
        }, 200); // Slightly longer delay to ensure DOM is ready
      }

      // Update button styles
      const buttons = {
        0: document.getElementById('menu-btn'),
        1: document.getElementById('page1-btn'),
        2: document.getElementById('page2-btn'),
        3: document.getElementById('page3-btn'),
        4: document.getElementById('page4-btn')
      };

      // Reset all buttons
      Object.values(buttons).forEach(btn => {
        if (btn) {
          btn.style.background = '#000';
          btn.style.boxShadow = '0 0 5px #0f0';
        }
      });

      // Highlight active button
      if (buttons[pageNum]) {
        buttons[pageNum].style.background = '#030';
        buttons[pageNum].style.boxShadow = '0 0 15px #0f0';
      }

      log(`Switched to Page ${pageNum}`);
    }

    // PACKET INJECTION MODE
    let injectionMode = false;
    function toggleInjectionMode() {
      injectionMode = !injectionMode;
      const btn = document.getElementById('injection-mode-btn');

      if (injectionMode) {
        btn.textContent = 'INJECTION: ON';
        btn.style.borderColor = '#f33';
        btn.style.color = '#f33';
        btn.style.boxShadow = '0 0 15px #f33';
        log('⚠️ PACKET INJECTION MODE ENABLED');
        showNotification('Injection mode ENABLED - Use responsibly!');
      } else {
        btn.textContent = 'INJECTION: OFF';
        btn.style.borderColor = '#f90';
        btn.style.color = '#f90';
        btn.style.boxShadow = '0 0 5px #f90';
        log('Packet injection mode disabled');
        showNotification('Injection mode disabled');
      }
    }

    // LAUNCH PENTEST TOOL
    function launchTool(toolName) {
      log(`Launching ${toolName}...`);

      const output = document.getElementById('page2-output');
      output.textContent = `🎯 Launching ${toolName}...\\n\\n`;

      // Real tool launch via backend
      fetch('/tools/launch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tool: toolName, injection_mode: injectionMode})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          output.textContent += `✓ ${toolName} initialized\\n`;
          output.textContent += `\\n${data.info || ''}\\n`;
          output.textContent += `\\nTool ready. Configure options and execute.\\n`;
          if (data.command) {
            output.textContent += `\\nCommand: ${data.command}\\n`;
          }
          showNotification(`${toolName} ready`);
        } else {
          output.textContent += `✗ Error: ${data.error || 'Unknown error'}\\n`;
          showNotification(`${toolName} failed to launch`);
        }
      })
      .catch(err => {
        output.textContent += `✗ Network error: ${err}\\n`;
        showNotification('Tool launch error');
      });
    }

    function updateSystemMonitor(nodeCount) {
      // Simple algorithm to make the bars move based on node count
      const count = nodeCount || 0;
      const cpu = 10 + count * 20;
      const memory = 15 + count * 15;
      const disk = 25 + count * 10;
      const network = 5 + count * 25;

      document.getElementById('cpu-progress').style.width = `${Math.min(95, cpu)}%`;
      document.getElementById('memory-progress').style.width = `${Math.min(95, memory)}%`;
      document.getElementById('disk-progress').style.width = `${Math.min(95, disk)}%`;
      document.getElementById('network-progress').style.width = `${Math.min(95, network)}%`;
    }
    
    function updateNetworkMap(nodes) {
      const map = document.getElementById('network-map');
      map.innerHTML = '';
      
      if (!nodes) return;
      
      const nodeIds = Object.keys(nodes);
      document.getElementById('node-count').textContent = nodeIds.length;
      
      // Always add master node
      const master = document.createElement('div');
      master.className = 'node';
      master.textContent = 'M';
      master.title = 'Master Node';
      master.style.left = '40px';
      master.style.top = '150px';
      map.appendChild(master);
      
      // Add peer nodes
      nodeIds.forEach((id, index) => {
        const x = 150 + index * 100;
        const y = 80 + (index % 3) * 80;
        
        const node = document.createElement('div');
        node.className = 'node';
        node.textContent = 'P';
        node.title = id;
        node.style.left = `${x}px`;
        node.style.top = `${y}px`;
        map.appendChild(node);
        
        // Add connection to master
        const conn = document.createElement('div');
        conn.className = 'connection';
        conn.style.width = `${Math.sqrt((x-40)*(x-40) + (y-150)*(y-150))}px`;
        conn.style.left = '40px';
        conn.style.top = '150px';
        conn.style.transform = `rotate(${Math.atan2(y-150, x-40) * 180 / Math.PI}deg)`;
        map.appendChild(conn);
      });
    }
    
    function updateStatus() {
      fetch('/status')
      .then(response => response.json())
      .then(data => {
        // Update node display
        updateSystemMonitor(Object.keys(data.nodes || {}).length);
        updateNetworkMap(data.nodes);
        
        // Update status
        document.getElementById('status').textContent = data.status || 'OFFLINE';
        
        // Update OS name based on device ID
        const deviceId = data.device_id || '';
        if (deviceId.startsWith('android_')) {
          document.getElementById('os').textContent = 'Android';
        } else if (deviceId.startsWith('win_')) {
          document.getElementById('os').textContent = 'Windows';
        } else if (deviceId.startsWith('linux_')) {
          document.getElementById('os').textContent = 'Linux';
        }
        
        // Update role based on authority and is_master flag
        const isMaster = data.is_master === true || data.authority === data.device_id || data.authority === 'local_device';
        console.log('[DEBUG] Role update:', {
          authority: data.authority,
          device_id: data.device_id,
          is_master: data.is_master,
          mode: data.mode,
          calculated_isMaster: isMaster
        });
        
        if (isMaster) {
          document.getElementById('role').textContent = "[MASTER NODE]";
        } else {
          document.getElementById('role').textContent = "[PEER NODE]";
        }
        
        // Update network mode (HOME_LAN or AWAY)
        const networkMode = data.network_mode || 'AWAY';
        const homeSubnet = data.home_network_subnet || '';
        const networkModeEl = document.getElementById('network-mode');
        const networkModeItem = document.getElementById('network-mode-item');

        // Remove all network mode classes
        if (networkModeItem) {
          networkModeItem.classList.remove('home-lan', 'away');

          if (networkMode === 'HOME_LAN') {
            networkModeEl.textContent = `🏠 HOME`;
            networkModeEl.style.color = '#0f0';
            networkModeItem.classList.add('home-lan');
          } else {
            networkModeEl.textContent = `🌐 AWAY`;
            networkModeEl.style.color = '#f90';
            networkModeItem.classList.add('away');
          }
        }

        // Update connection status
        const connectionStatus = data.connection_status || 'standalone';
        const standaloneMode = data.standalone_mode !== false;
        const pendingSync = data.pending_sync || 0;
        const connectionStatusEl = document.getElementById('connection-status');
        const connectionStatusItem = document.getElementById('connection-status-item');

        // Remove all status classes
        if (connectionStatusItem) {
          connectionStatusItem.classList.remove('connected', 'standalone', 'connecting');

          if (connectionStatus === 'connected') {
            connectionStatusEl.textContent = `CONNECTED${pendingSync > 0 ? ` (${pendingSync} queued)` : ''}`;
            connectionStatusEl.style.color = '#0f0';
            connectionStatusItem.classList.add('connected');
          } else if (connectionStatus === 'connecting') {
            connectionStatusEl.textContent = 'CONNECTING...';
            connectionStatusEl.style.color = '#33f';
            connectionStatusItem.classList.add('connecting');
          } else {
            connectionStatusEl.textContent = `STANDALONE${pendingSync > 0 ? ` (${pendingSync} queued)` : ''}`;
            connectionStatusEl.style.color = '#ff0';
            connectionStatusItem.classList.add('standalone');
          }
        }

        // Update tunnel status
        const tunnelStatus = data.tunnel || {active: false};
        const tunnelStatusEl = document.getElementById('tunnel-status');
        const startBtn = document.getElementById('start-tunnel-btn');
        const stopBtn = document.getElementById('stop-tunnel-btn');
        const tunnelStatusItem = tunnelStatusEl.parentElement;
        
        if (tunnelStatus.active) {
          tunnelStatusEl.textContent = 'ACTIVE';
          tunnelStatusEl.style.color = '#0f0';
          tunnelStatusItem.classList.add('tunnel-active');
          startBtn.style.display = 'none';
          stopBtn.style.display = 'inline-block';
          
          // Show tunnel info if available
          if (tunnelStatus.mesh_id) {
            const peerCount = Object.keys(tunnelStatus.peers || {}).length;
            tunnelStatusEl.textContent = `ACTIVE (${peerCount} peers)`;
          }
        } else {
          tunnelStatusEl.textContent = 'OFFLINE';
          tunnelStatusEl.style.color = '#f33';
          tunnelStatusItem.classList.remove('tunnel-active');
          startBtn.style.display = 'inline-block';
          stopBtn.style.display = 'none';
        }

        // PHASE 2: Update control button based on authority
        const authority = data.authority;
        const authorityName = data.authority_device_name;

        // Determine button state
        if (authority) {
          if (authority === deviceId || authority === 'local_device') {
            // This device has control
            updateControlButton(true, 'local_device', null);
          } else {
            // Another device has control
            updateControlButton(false, authority, authorityName);
          }
        } else {
          // No one has control
          updateControlButton(false, null, null);
        }

        // Update tool state if needed
        if (data.tool && data.tool !== currentTool) {
          currentTool = data.tool;
          log(`Tool changed to: ${data.tool}`);
        }
        
        // Check if sync happened
        if (data.last_sync && data.last_sync * 1000 > lastSync) {
          lastSync = data.last_sync * 1000;
          log(`Sync occurred at ${new Date(lastSync).toLocaleTimeString()}`);
        }
        
        // Log connection status changes (track previous status)
        const prevConnectionStatus = window.lastConnectionStatus || 'standalone';
        window.lastConnectionStatus = connectionStatus;
        if (connectionStatus !== prevConnectionStatus) {
          if (connectionStatus === 'connected') {
            log('Connected to master node');
            if (pendingSync > 0) {
              log(`Processing ${pendingSync} queued sync operations...`);
            }
          } else if (connectionStatus === 'standalone') {
            log('Operating in standalone mode');
          } else if (connectionStatus === 'connecting') {
            log('Attempting to connect to master...');
          }
        }
      })
      .catch(error => {
        document.getElementById('status').textContent = 'ERROR';
      });
    }

    // ESC key to close modals
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' || e.key === 'Esc') {
        closeCodeViewer();
        closeToolModal();
      }
    });

    // DEVELOPER MODE: Auto-authenticate as KingKali on load
    function autoAuthenticate() {
      authenticated = true;
      document.getElementById('auth-btn').classList.add('active');
      document.getElementById('auth-btn').textContent = '👑 KING KALI';
      document.getElementById('auth-btn').style.background = '#030';
      document.getElementById('auth-btn').style.boxShadow = '0 0 15px #0f0';
      log('👑 Developer Mode: Auto-authenticated as KingKali - Full Master Access');
      showNotification('👑 KingKali - Developer Mode Active');
      
      // Auto-set developer tier
      fetch('/ghost/tier/set', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tier: 'DEVELOPER', passphrase: 'kingkali'})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          log(`✅ Tier set to: ${data.tier}`);
        }
      })
      .catch(e => console.log('Tier set (optional):', e));
    }
    
    // Initialize
    autoAuthenticate();  // Auto-auth on load
    updateStatus();

    // Poll for updates
    setInterval(updateStatus, 2000);

    // ═══════════════════════════════════════════════════════════════
    // GHOST AGENT - Floating AI Assistant
    // ═══════════════════════════════════════════════════════════════
    
    const Ghost = {
      isListening: false,
      recognition: null,
      synthesis: window.speechSynthesis,
      conversationHistory: [],  // MAINTAIN CONVERSATION STATE
      
      init() {
        this.injectHTML();
        this.initSpeech();
        console.log('👻 Ghost Agent initialized');
        // Add initial system message
        this.conversationHistory.push({
          role: 'system',
          content: 'You are Ghost, the AI partner of King Kali, developer of GhostHUD. Developer mode - full access.'
        });
      },
      
      injectHTML() {
        const ghostHTML = `
          <div class="ghost-float">
            <div class="ghost-avatar" onclick="Ghost.togglePanel()" title="Talk to Ghost">
              <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <radialGradient id="ghostGrad" cx="50%" cy="30%">
                    <stop offset="0%" style="stop-color:#0d2a0d"/>
                    <stop offset="100%" style="stop-color:#050a05"/>
                  </radialGradient>
                </defs>
                <rect fill="url(#ghostGrad)" width="100" height="100"/>
                <path d="M50 10c-18 0-30 14-30 35v30c0 6 4 12 10 14l20 9 20-9c6-2 10-8 10-14V45c0-21-12-35-30-35z" fill="#0a150a" stroke="#0f0" stroke-width="1.5"/>
                <ellipse cx="38" cy="50" rx="7" ry="10" fill="#0f0" opacity=".9" filter="url(#outerGlow)"/>
                <ellipse cx="62" cy="50" rx="7" ry="10" fill="#0f0" opacity=".9" filter="url(#outerGlow)"/>
                <ellipse cx="40" cy="47" rx="2" ry="3" fill="#fff" opacity=".8"/>
                <ellipse cx="64" cy="47" rx="2" ry="3" fill="#fff" opacity=".8"/>
              </svg>
              <div class="ghost-status"></div>
            </div>
          </div>
          
          <div id="ghost-panel" class="ghost-panel">
            <div class="ghost-panel-header">
              <span class="ghost-panel-title">👻 GHOST AGENT</span>
              <div style="display:flex;gap:10px;align-items:center">
                <button id="ghost-tts-toggle" class="ghost-tts-btn" onclick="Ghost.toggleTTS()" title="Toggle Text-to-Speech">🔊</button>
                <button class="ghost-panel-close" onclick="Ghost.togglePanel()">×</button>
              </div>
            </div>
            <div id="ghost-messages" class="ghost-messages">
              <div class="ghost-msg ghost">I am Ghost. How may I assist you?</div>
            </div>
            <div id="ghost-typing" class="ghost-typing">
              <div class="ghost-dot"></div>
              <div class="ghost-dot"></div>
              <div class="ghost-dot"></div>
            </div>
            <div class="ghost-input-area">
              <input type="text" id="ghost-input" class="ghost-input" placeholder="Type or speak..." onkeypress="if(event.key==='Enter')Ghost.send()">
              <button id="ghost-mic" class="ghost-btn" onclick="Ghost.toggleMic()" title="Voice">MIC</button>
              <button class="ghost-btn" onclick="Ghost.send()" title="Send">GO</button>
            </div>
          </div>
        `;
        document.body.insertAdjacentHTML('beforeend', ghostHTML);
      },
      
      initSpeech() {
        // Check for speech recognition support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
          console.log('[GHOST] Speech recognition not supported in this browser');
          return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;  // Simplified - just get final result
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        this.recognition.onstart = () => {
          console.log('[GHOST] Speech recognition started');
          document.getElementById('ghost-input').placeholder = 'Listening...';
        };
        
        this.recognition.onresult = (event) => {
          console.log('[GHOST] Got speech result');
          const transcript = event.results[0][0].transcript;
          console.log('[GHOST] Transcript:', transcript);
          document.getElementById('ghost-input').value = transcript;
          this.send(transcript);
        };
        
        this.recognition.onend = () => {
          console.log('[GHOST] Speech recognition ended');
          this.stopListening();
        };
        
        this.recognition.onerror = (event) => {
          console.error('[GHOST] Speech error:', event.error, event);
          this.stopListening();
          
          switch(event.error) {
            case 'not-allowed':
            case 'permission-denied':
              this.addMsg('ghost', 'Mic blocked. Click lock icon in address bar > Allow microphone.');
              break;
            case 'no-speech':
              this.addMsg('ghost', "Didn't hear anything. Try again?");
              break;
            case 'network':
              // Try alternative approach
              this.addMsg('ghost', 'Speech service unavailable. Using backup...');
              this.tryAlternativeSpeech();
              break;
            case 'aborted':
              // User cancelled, no message needed
              break;
            default:
              this.addMsg('ghost', 'Voice issue: ' + event.error + '. Try typing instead.');
          }
        };
        
        console.log('[GHOST] Speech recognition initialized');
      },
      
      tryAlternativeSpeech() {
        // Fallback message - the network error usually means Google's servers are blocked
        this.addMsg('ghost', "Brave browser blocks Google's speech servers by default. Options: 1) Type your message, 2) Try Chrome browser, 3) Disable Brave shields for this site.");
      },
      
      togglePanel() {
        const panel = document.getElementById('ghost-panel');
        panel.classList.toggle('show');
        if (panel.classList.contains('show')) {
          document.getElementById('ghost-input').focus();
        }
      },
      
      toggleMic() {
        if (this.isListening) {
          this.stopListening();
        } else {
          this.startListening();
        }
      },
      
      startListening() {
        if (!this.recognition) {
          this.addMsg('ghost', 'Voice not supported. Please type your message.');
          return;
        }
        
        // Already listening? Stop first
        if (this.isListening) {
          this.stopListening();
          return;
        }
        
        console.log('[GHOST] Starting speech recognition...');
        this.isListening = true;
        document.getElementById('ghost-mic').classList.add('recording');
        document.getElementById('ghost-mic').textContent = 'REC';
        document.querySelector('.ghost-avatar').classList.add('listening');
        
        try { 
          this.recognition.start();
        } catch(e) { 
          console.error('[GHOST] Recognition start error:', e);
          this.stopListening();
          if (e.message && e.message.includes('already started')) {
            this.addMsg('ghost', 'Mic is busy. Wait a moment and try again.');
          } else {
            this.addMsg('ghost', 'Could not start mic: ' + e.message);
          }
        }
      },
      
      stopListening() {
        console.log('[GHOST] Stopping speech recognition');
        this.isListening = false;
        const micBtn = document.getElementById('ghost-mic');
        if (micBtn) {
          micBtn.classList.remove('recording');
          micBtn.textContent = 'MIC';
        }
        const input = document.getElementById('ghost-input');
        if (input) input.placeholder = 'Type or speak...';
        const avatar = document.querySelector('.ghost-avatar');
        if (avatar) avatar.classList.remove('listening');
        if (this.recognition) {
          try { this.recognition.stop(); } catch(e) { console.log('[GHOST] Stop error (ok):', e); }
        }
      },
      
      speak(text) {
        if (!this.ttsEnabled || !this.synthesis) return;
        this.synthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1; u.pitch = 0.8;
        const voices = this.synthesis.getVoices();
        const voice = voices.find(v => v.name.includes('Daniel') || v.name.includes('Google UK English Male')) || voices.find(v => v.lang.startsWith('en'));
        if (voice) u.voice = voice;
        u.onstart = () => document.querySelector('.ghost-avatar').classList.add('speaking');
        u.onend = () => document.querySelector('.ghost-avatar').classList.remove('speaking');
        this.synthesis.speak(u);
      },
      
      toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        localStorage.setItem('ghost_tts_enabled', this.ttsEnabled);
        this.updateTTSToggle();
        if (this.ttsEnabled) {
          this.addMsg('ghost', '🔊 Text-to-speech enabled');
        } else {
          this.synthesis.cancel();  // Stop any current speech
          this.addMsg('ghost', '🔇 Text-to-speech disabled');
        }
      },
      
      updateTTSToggle() {
        const btn = document.getElementById('ghost-tts-toggle');
        if (btn) {
          btn.textContent = this.ttsEnabled ? '🔊' : '🔇';
          btn.classList.toggle('muted', !this.ttsEnabled);
        }
      },
      
      async send(text = null) {
        const input = document.getElementById('ghost-input');
        const msg = text || input.value.trim();
        if (!msg) return;
        
        // Add user message to conversation history
        this.conversationHistory.push({role: 'user', content: msg});
        this.addMsg('user', msg);
        input.value = '';
        this.showTyping(true);
        
        console.log('[GHOST] Conversation history:', this.conversationHistory.length, 'messages');
        console.log('[GHOST] Sending full history to backend');
        
        try {
          // Send FULL conversation history to backend
          const res = await fetch('/ghost/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              message: msg,
              conversation_history: this.conversationHistory  // SEND FULL HISTORY
            })
          });
          const data = await res.json();
          this.showTyping(false);
          const reply = data.response || data.message || 'Ghost is processing...';
          
          // Add assistant response to conversation history
          this.conversationHistory.push({role: 'assistant', content: reply});
          
          this.addMsg('ghost', reply);
          this.speak(reply);
        } catch(e) {
          this.showTyping(false);
          const reply = this.fallback(msg);
          this.conversationHistory.push({role: 'assistant', content: reply});
          this.addMsg('ghost', reply);
          this.speak(reply);
        }
      },
      
      fallback(msg) {
        const m = msg.toLowerCase();
        if (m.includes('hello') || m.includes('hi') || m.includes('hey')) return "Hello, operator. Ghost Agent online. How can I help?";
        if (m.includes('who are you')) return "I am Ghost, your TRINITY AI agent. Ghost Core for cognition, Echo Core for behavior, Shell Core for system control.";
        if (m.includes('help')) return "I can assist with security ops, recon, analysis, and system control. What do you need?";
        if (m.includes('status')) return "All systems nominal. Ghost Core: ACTIVE. Echo Core: MONITORING. Shell Core: READY.";
        if (m.includes('scan') || m.includes('nmap')) return "Network scanning ready. Use the Tool Library above to launch scans.";
        if (m.includes('hack') || m.includes('pentest')) return "Penetration testing tools available in Page 2. Ethical use only.";
        return "Acknowledged: " + msg + ". Ghost processing...";
      },
      
      addMsg(sender, text) {
        const msgs = document.getElementById('ghost-messages');
        const div = document.createElement('div');
        div.className = 'ghost-msg ' + sender;
        div.textContent = text;
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
      },
      
      showTyping(show) {
        document.getElementById('ghost-typing').classList.toggle('show', show);
      }
    };
    
    // ============================================
    // GHOSTVERSE CONTROL ROOM FUNCTIONS
    // ============================================
    let battleActive = false;
    let battleMode = null;
    let battleStartTime = null;
    let networkCanvas = null;
    let radarCanvas = null;
    let radarBlips = [];
    
    function selectBattleMode(mode) {
      // Update mode buttons
      document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById(`mode-${mode}`).classList.add('active');
      
      // Start battle
      startBattleMode(mode);
    }
    
    function startBattleMode(mode) {
      battleMode = mode;
      battleActive = true;
      battleStartTime = Date.now();
      
      // Update opponent avatar screen
      const opponentStatus = document.getElementById('opponent-status');
      if (mode === 'ai') {
        opponentStatus.textContent = 'AI CHAMPION';
        document.querySelector('.avatar-placeholder').textContent = '🤖';
      } else if (mode === 'p2p') {
        opponentStatus.textContent = 'CONNECTING...';
        document.querySelector('.avatar-placeholder').textContent = '👥';
      } else {
        opponentStatus.textContent = 'PRACTICE MODE';
        document.querySelector('.avatar-placeholder').textContent = '🎮';
      }
      
      // Initialize visualizations
      initNetworkMap();
      initRadar();
      
      // Start battle
      fetch('/battle/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({mode: mode})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          addSpectatorComment('[SYSTEM]', `Battle started: ${mode.toUpperCase()} mode`);
          addSpectatorComment('[SYSTEM]', data.message || 'Battle in progress...');
          updateBattleStatus();
        } else {
          addSpectatorComment('[ERROR]', data.message || 'Failed to start battle');
        }
      })
      .catch(e => {
        addSpectatorComment('[ERROR]', `Connection error: ${e.message}`);
      });
      
      log(`🏛️ Ghostverse: Starting ${mode} battle`);
    }
    
    function initNetworkMap() {
      const canvas = document.getElementById('network-canvas');
      if (!canvas) {
        console.warn('[Control Room] Network canvas not found');
        return;
      }
      
      try {
        networkCanvas = canvas.getContext('2d');
        if (!networkCanvas) {
          console.warn('[Control Room] Could not get 2D context');
          return;
        }
        
        function resizeCanvas() {
          const rect = canvas.parentElement.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            canvas.width = rect.width;
            canvas.height = rect.height;
            drawNetworkMap();
          }
        }
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        console.log('[Control Room] Network map initialized');
      } catch (e) {
        console.error('[Control Room] Network map init error:', e);
      }
    }
    
    function drawNetworkMap() {
      if (!networkCanvas) return;
      
      const canvas = networkCanvas.canvas;
      networkCanvas.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw connections
      networkCanvas.strokeStyle = '#00ffff';
      networkCanvas.globalAlpha = 0.4;
      networkCanvas.lineWidth = 2;
      
      const nodes = [
        {x: canvas.width * 0.2, y: canvas.height * 0.3},
        {x: canvas.width * 0.5, y: canvas.height * 0.2},
        {x: canvas.width * 0.8, y: canvas.height * 0.3},
        {x: canvas.width * 0.3, y: canvas.height * 0.7},
        {x: canvas.width * 0.7, y: canvas.height * 0.7},
        {x: canvas.width * 0.5, y: canvas.height * 0.5}
      ];
      
      // Draw connections
      nodes.forEach((node, i) => {
        if (i < nodes.length - 1) {
          networkCanvas.beginPath();
          networkCanvas.moveTo(node.x, node.y);
          networkCanvas.lineTo(nodes[i + 1].x, nodes[i + 1].y);
          networkCanvas.stroke();
        }
      });
      
      // Draw nodes
      networkCanvas.globalAlpha = 1;
      nodes.forEach(node => {
        networkCanvas.beginPath();
        networkCanvas.arc(node.x, node.y, 8, 0, Math.PI * 2);
        networkCanvas.fillStyle = '#00ffff';
        networkCanvas.fill();
        networkCanvas.shadowBlur = 15;
        networkCanvas.shadowColor = '#00ffff';
        networkCanvas.fill();
        networkCanvas.shadowBlur = 0;
      });
      
      requestAnimationFrame(drawNetworkMap);
    }
    
    function initRadar() {
      const canvas = document.getElementById('radar-canvas');
      if (!canvas) {
        console.warn('[Control Room] Radar canvas not found');
        return;
      }
      
      try {
        radarCanvas = canvas.getContext('2d');
        if (!radarCanvas) {
          console.warn('[Control Room] Could not get 2D context for radar');
          return;
        }
        
        function resizeCanvas() {
          const rect = canvas.parentElement.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            canvas.width = rect.width;
            canvas.height = rect.height;
          }
        }
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Initialize blips
        radarBlips = [
          {angle: Math.PI * 0.3, distance: 0.4, type: 'attack'},
          {angle: Math.PI * 0.7, distance: 0.6, type: 'defense'},
          {angle: Math.PI * 1.2, distance: 0.3, type: 'recon'}
        ];
        
        drawRadar();
        console.log('[Control Room] Radar initialized');
      } catch (e) {
        console.error('[Control Room] Radar init error:', e);
      }
    }
    
    function drawRadar() {
      if (!radarCanvas) return;
      
      const canvas = radarCanvas.canvas;
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const radius = Math.min(centerX, centerY) - 20;
      
      radarCanvas.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw sweep line
      const sweepAngle = (Date.now() / 20) % (Math.PI * 2);
      radarCanvas.strokeStyle = '#00ffff';
      radarCanvas.lineWidth = 2;
      radarCanvas.globalAlpha = 0.6;
      radarCanvas.beginPath();
      radarCanvas.moveTo(centerX, centerY);
      radarCanvas.lineTo(
        centerX + Math.cos(sweepAngle) * radius,
        centerY + Math.sin(sweepAngle) * radius
      );
      radarCanvas.stroke();
      
      // Draw blips
      radarCanvas.globalAlpha = 1;
      radarBlips.forEach(blip => {
        const x = centerX + Math.cos(blip.angle) * (radius * blip.distance);
        const y = centerY + Math.sin(blip.angle) * (radius * blip.distance);
        
        radarCanvas.beginPath();
        radarCanvas.arc(x, y, 6, 0, Math.PI * 2);
        radarCanvas.fillStyle = blip.type === 'attack' ? '#ff00ff' : blip.type === 'defense' ? '#0040ff' : '#00ffff';
        radarCanvas.fill();
        radarCanvas.shadowBlur = 15;
        radarCanvas.shadowColor = radarCanvas.fillStyle;
        radarCanvas.fill();
        radarCanvas.shadowBlur = 0;
      });
      
      requestAnimationFrame(drawRadar);
    }
    
    // ============================================
    // 13 GHOSTS HOUSE RENDERER - Cyberpunk Theme
    // ============================================
    let houseCanvas = null;
    let houseCtx = null;
    let currentHouseRoom = 1;
    let houseWalls = [];
    let houseDoors = [];
    let houseAnimations = [];
    
    function initHouseRenderer() {
      const canvas = document.getElementById('house-canvas');
      if (!canvas) {
        console.warn('[House] Canvas not found');
        return;
      }
      
      try {
        houseCanvas = canvas;
        houseCtx = canvas.getContext('2d');
        
        function resizeCanvas() {
          const rect = canvas.parentElement.getBoundingClientRect();
          canvas.width = rect.width;
          canvas.height = rect.height;
          renderHouse();
        }
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Initialize room 1
        initializeRoom(1);
        renderHouse();
        
        // Start animation loop
        animateHouse();
        
        console.log('[House] 13 Ghosts House initialized');
      } catch (e) {
        console.error('[House] Init error:', e);
      }
    }
    
    function initializeRoom(roomId) {
      currentHouseRoom = roomId;
      const roomDisplay = document.getElementById('current-room-display');
      if (roomDisplay) roomDisplay.textContent = roomId;
      
      // Reset room state
      houseWalls = [];
      houseDoors = [];
      houseAnimations = [];
      
      // Create walls for room (4 walls in a square)
      const wallPositions = [
        {x: 0, y: 0, width: houseCanvas.width, height: 3, side: 'top'},
        {x: 0, y: houseCanvas.height - 3, width: houseCanvas.width, height: 3, side: 'bottom'},
        {x: 0, y: 0, width: 3, height: houseCanvas.height, side: 'left'},
        {x: houseCanvas.width - 3, y: 0, width: 3, height: houseCanvas.height, side: 'right'}
      ];
      
      houseWalls = wallPositions.map((pos, i) => ({
        ...pos,
        id: `wall_${i}`,
        color: '#ff00ff',
        glow: 0.3,
        shifting: false
      }));
    }
    
    function renderHouse() {
      if (!houseCtx || !houseCanvas) return;
      
      // Clear canvas
      houseCtx.fillStyle = '#0a0a0a';
      houseCtx.fillRect(0, 0, houseCanvas.width, houseCanvas.height);
      
      // Draw grid floor
      drawGridFloor();
      
      // Draw walls
      houseWalls.forEach(wall => drawWall(wall));
      
      // Draw doors
      houseDoors.forEach(door => drawDoor(door));
      
      // Draw room number
      houseCtx.fillStyle = '#00ffff';
      houseCtx.font = 'bold 16px monospace';
      houseCtx.textAlign = 'center';
      houseCtx.fillText(`ROOM ${currentHouseRoom}`, houseCanvas.width / 2, 20);
    }
    
    function drawGridFloor() {
      houseCtx.strokeStyle = 'rgba(0, 255, 255, 0.1)';
      houseCtx.lineWidth = 1;
      
      const gridSize = 20;
      for (let x = 0; x < houseCanvas.width; x += gridSize) {
        houseCtx.beginPath();
        houseCtx.moveTo(x, 0);
        houseCtx.lineTo(x, houseCanvas.height);
        houseCtx.stroke();
      }
      for (let y = 0; y < houseCanvas.height; y += gridSize) {
        houseCtx.beginPath();
        houseCtx.moveTo(0, y);
        houseCtx.lineTo(houseCanvas.width, y);
        houseCtx.stroke();
      }
    }
    
    function drawWall(wall) {
      // Wall with neon glow
      const glow = wall.glow || 0.3;
      
      // Outer glow
      houseCtx.shadowBlur = 15;
      houseCtx.shadowColor = wall.color;
      houseCtx.fillStyle = wall.color;
      houseCtx.fillRect(wall.x, wall.y, wall.width, wall.height);
      
      // Inner highlight
      houseCtx.shadowBlur = 0;
      houseCtx.fillStyle = '#ffffff';
      houseCtx.fillRect(wall.x + 1, wall.y + 1, Math.max(1, wall.width - 2), Math.max(1, wall.height - 2));
      
      // If shifting, add trail
      if (wall.shifting) {
        houseCtx.fillStyle = `rgba(255, 0, 255, ${glow})`;
        houseCtx.fillRect(wall.x - 5, wall.y - 5, wall.width + 10, wall.height + 10);
      }
    }
    
    function drawDoor(door) {
      const {x, y, width, height, color, glow, pulse} = door;
      
      // Door glow
      houseCtx.shadowBlur = 20;
      houseCtx.shadowColor = color;
      houseCtx.fillStyle = color;
      
      // Pulse animation
      const pulseAlpha = pulse ? 0.3 + Math.sin(Date.now() / 300) * 0.2 : 0.5;
      houseCtx.globalAlpha = pulseAlpha;
      
      houseCtx.fillRect(x, y, width, height);
      
      // Door frame
      houseCtx.shadowBlur = 0;
      houseCtx.globalAlpha = 1;
      houseCtx.strokeStyle = '#ffffff';
      houseCtx.lineWidth = 2;
      houseCtx.strokeRect(x, y, width, height);
      
      // Service label
      if (door.service) {
        houseCtx.fillStyle = '#00ffff';
        houseCtx.font = '10px monospace';
        houseCtx.textAlign = 'center';
        houseCtx.fillText(door.service, x + width / 2, y + height / 2 + 3);
      }
    }
    
    function animateHouse() {
      // Update animations
      houseAnimations = houseAnimations.filter(anim => {
        anim.progress += 0.016; // ~60fps
        return anim.progress < 1.0;
      });
      
      // Update door pulses
      houseDoors.forEach(door => {
        if (door.pulse) {
          door.glow = 0.3 + Math.sin(Date.now() / 300) * 0.2;
        }
      });
      
      // Re-render
      renderHouse();
      
      // Draw particles
      drawParticles();
      
      requestAnimationFrame(animateHouse);
    }
    
    function drawParticles() {
      houseAnimations.forEach(anim => {
        if (anim.type === 'particle') {
          const alpha = 1 - anim.progress;
          const size = 3 * (1 - anim.progress);
          
          houseCtx.save();
          houseCtx.globalAlpha = alpha;
          houseCtx.fillStyle = anim.color || '#00ff41';
          houseCtx.shadowBlur = 10;
          houseCtx.shadowColor = anim.color || '#00ff41';
          
          const x = anim.x + (anim.vx || 0) * anim.progress * 100;
          const y = anim.y + (anim.vy || 0) * anim.progress * 100;
          
          houseCtx.beginPath();
          houseCtx.arc(x, y, size, 0, Math.PI * 2);
          houseCtx.fill();
          houseCtx.restore();
        }
      });
    }
    
    // Visual effect handlers
    function handleVisualEffect(effect) {
      console.log('[House] Visual effect:', effect);
      
      const statusEl = document.getElementById('house-status');
      if (statusEl) statusEl.textContent = effect.message || 'Effect triggered';
      
      switch (effect.type) {
        case 'doors_spawn':
          spawnDoors(effect.doors || []);
          break;
        case 'walls_shift':
          shiftWalls(effect.pattern || 'shuffle');
          break;
        case 'floor_drop':
          dropFloor(effect.level || 1);
          break;
        case 'door_disappear':
          removeDoors(effect.doors || []);
          break;
        case 'particle_explosion':
          createExplosion(effect);
          break;
      }
    }
    
    function spawnDoors(doors) {
      doors.forEach((doorData, i) => {
        const position = doorData.position || 'north';
        const {x, y, width, height} = getDoorPosition(position, i);
        
        const door = {
          id: doorData.id || `door_${i}`,
          x, y, width: 40, height: 60,
          color: doorData.glow_color || '#00ffff',
          glow: 0.5,
          pulse: true,
          service: doorData.service || doorData.port || '',
          spawnTime: Date.now()
        };
        
        // Fade-in animation
        door.glow = 0;
        houseAnimations.push({
          type: 'fade_in',
          target: door,
          progress: 0,
          duration: 1000
        });
        
        houseDoors.push(door);
      });
    }
    
    function shiftWalls(pattern) {
      houseWalls.forEach(wall => {
        wall.shifting = true;
        wall.glow = 0.8;
        
        // Animate shift
        houseAnimations.push({
          type: 'wall_shift',
          target: wall,
          pattern: pattern,
          progress: 0,
          duration: 2000
        });
      });
      
      setTimeout(() => {
        houseWalls.forEach(wall => {
          wall.shifting = false;
          wall.glow = 0.3;
        });
      }, 2000);
    }
    
    function dropFloor(level) {
      // Create particle explosion
      for (let i = 0; i < 20; i++) {
        houseAnimations.push({
          type: 'particle',
          x: houseCanvas.width / 2 + (Math.random() - 0.5) * 100,
          y: houseCanvas.height / 2 + (Math.random() - 0.5) * 100,
          vx: (Math.random() - 0.5) * 5,
          vy: (Math.random() - 0.5) * 5,
          color: '#00ff41',
          progress: 0,
          duration: 1000
        });
      }
    }
    
    function removeDoors(doorIds) {
      houseDoors = houseDoors.filter(door => !doorIds.includes(door.id));
    }
    
    function createExplosion(effect) {
      const color = effect.color || '#ff0040';
      for (let i = 0; i < 30; i++) {
        houseAnimations.push({
          type: 'particle',
          x: houseCanvas.width / 2,
          y: houseCanvas.height / 2,
          vx: (Math.random() - 0.5) * 8,
          vy: (Math.random() - 0.5) * 8,
          color: color,
          progress: 0,
          duration: 1500
        });
      }
    }
    
    function getDoorPosition(position, index) {
      const margin = 20;
      const doorWidth = 40;
      const doorHeight = 60;
      
      switch (position) {
        case 'north':
          return {x: margin + index * 60, y: margin, width: doorWidth, height: doorHeight};
        case 'south':
          return {x: margin + index * 60, y: houseCanvas.height - margin - doorHeight, width: doorWidth, height: doorHeight};
        case 'east':
          return {x: houseCanvas.width - margin - doorWidth, y: margin + index * 60, width: doorWidth, height: doorHeight};
        case 'west':
          return {x: margin, y: margin + index * 60, width: doorWidth, height: doorHeight};
        default:
          return {x: margin, y: margin, width: doorWidth, height: doorHeight};
      }
    }
    
    function updateBattleStatus() {
      if (!battleActive) return;
      
      // Update time
      const elapsed = Math.floor((Date.now() - battleStartTime) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;
      document.getElementById('battle-time-display').textContent = 
        `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      
      fetch('/battle/status')
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          // Update scores
          document.getElementById('score-you').textContent = data.score_you || 0;
          document.getElementById('score-opponent').textContent = data.score_opponent || 0;
          
          // Update spectator feed
          if (data.spectators && Array.isArray(data.spectators)) {
            data.spectators.forEach(comment => {
              if (typeof comment === 'string') {
                addSpectatorComment('[SPECTATOR]', comment);
              }
            });
          }
          
          // Update system status
          updateSystemStatus(data);
        }
      })
      .catch(e => console.error('Battle status error:', e));
      
      if (battleActive) {
        setTimeout(updateBattleStatus, 2000);
      }
    }
    
    function addSpectatorComment(sender, message) {
      const feed = document.getElementById('spectator-feed-screen');
      const comment = document.createElement('div');
      comment.className = 'spectator-comment';
      comment.textContent = `${sender} ${message}`;
      feed.appendChild(comment);
      feed.scrollTop = feed.scrollHeight;
      
      // Limit to 50 comments
      while (feed.children.length > 50) {
        feed.removeChild(feed.firstChild);
      }
    }
    
    function updateSystemStatus(data) {
      // Update health, energy, etc. based on battle data
      const health = data.health || 100;
      const energy = data.energy || 85;
      
      document.getElementById('health-bar').style.width = health + '%';
      document.getElementById('health-value').textContent = health + '%';
      document.getElementById('energy-bar').style.width = energy + '%';
      document.getElementById('energy-value').textContent = energy + '%';
      
      const techniques = data.techniques_used || 0;
      document.getElementById('techniques-bar').style.width = Math.min(techniques * 10, 100) + '%';
      document.getElementById('techniques-value').textContent = techniques;
    }
    
    // Dashboard Button Functions
    function executeAttack(technique) {
      if (!battleActive) {
        addSpectatorComment('[SYSTEM]', 'Start a battle first!');
        return;
      }
      
      addSpectatorComment('[ACTION]', `Executing ${technique}...`);
      
      fetch('/battle/attack', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({technique: technique})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          addSpectatorComment('[SUCCESS]', `${technique} executed!`);
          
          // Trigger visual effect in house
          if (data.visual_effect) {
            handleVisualEffect(data.visual_effect);
          }
          
          // Add blip to radar
          radarBlips.push({
            angle: Math.random() * Math.PI * 2,
            distance: 0.3 + Math.random() * 0.4,
            type: 'attack'
          });
        } else {
          addSpectatorComment('[FAILED]', data.message || 'Attack failed');
        }
      })
      .catch(e => addSpectatorComment('[ERROR]', e.message));
    }
    
    function executeDefense(defenseType) {
      if (!battleActive) {
        addSpectatorComment('[SYSTEM]', 'Start a battle first!');
        return;
      }
      
      addSpectatorComment('[ACTION]', `Activating ${defenseType}...`);
      // Add defense blip
      radarBlips.push({
        angle: Math.random() * Math.PI * 2,
        distance: 0.5 + Math.random() * 0.3,
        type: 'defense'
      });
    }
    
    function executeRecon(reconType) {
      if (!battleActive) {
        addSpectatorComment('[SYSTEM]', 'Start a battle first!');
        return;
      }
      
      addSpectatorComment('[ACTION]', `Running ${reconType}...`);
      // Add recon blip
      radarBlips.push({
        angle: Math.random() * Math.PI * 2,
        distance: 0.2 + Math.random() * 0.5,
        type: 'recon'
      });
    }
    
    function executeDeploy(deployType) {
      if (!battleActive) {
        addSpectatorComment('[SYSTEM]', 'Start a battle first!');
        return;
      }
      
      addSpectatorComment('[ACTION]', `Deploying ${deployType}...`);
    }
    
    function executeAnalyze(analyzeType) {
      if (!battleActive) {
        addSpectatorComment('[SYSTEM]', 'Start a battle first!');
        return;
      }
      
      addSpectatorComment('[ACTION]', `Analyzing ${analyzeType}...`);
    }
    
    function executeCommand() {
      if (!battleActive) {
        addSpectatorComment('[SYSTEM]', 'Start a battle first!');
        return;
      }
      
      addSpectatorComment('[ACTION]', 'Executing command sequence...');
    }
    
    // ============================================
    // TRAINING FACILITY FUNCTIONS
    // ============================================
    function deployHoneypot() {
      const output = document.getElementById('training-output');
      output.textContent += '\\n[+] Deploying honeypot system...\\n';
      
      fetch('/honeypot/deploy', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({rooms: 3})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          output.textContent += `[+] Honeypot deployed! Session: ${data.session_id}\\n`;
          document.getElementById('honeypot-state').textContent = 'ONLINE';
          document.getElementById('honeypot-state').style.color = '#0f0';
        } else {
          output.textContent += `[!] Error: ${data.message}\\n`;
        }
        output.scrollTop = output.scrollHeight;
      })
      .catch(e => {
        output.textContent += `[!] Error: ${e.message}\\n`;
        output.scrollTop = output.scrollHeight;
      });
      
      log('🍯 Training: Deploying honeypot');
    }
    
    function checkHoneypotStatus() {
      fetch('/honeypot/status')
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          document.getElementById('honeypot-state').textContent = data.active ? 'ONLINE' : 'OFFLINE';
          document.getElementById('honeypot-state').style.color = data.active ? '#0f0' : '#666';
          
          const output = document.getElementById('training-output');
          output.textContent += `\\n[+] Honeypot Status: ${data.active ? 'ACTIVE' : 'INACTIVE'}\\n`;
          if (data.sessions) {
            output.textContent += `    Sessions: ${data.sessions}\\n`;
          }
          output.scrollTop = output.scrollHeight;
        }
      })
      .catch(e => console.error('Honeypot status error:', e));
    }
    
    function viewHoneypotLogs() {
      fetch('/honeypot/logs')
      .then(r => r.json())
      .then(data => {
        const output = document.getElementById('training-output');
        output.textContent = '\\n=== HONEYPOT LOGS ===\\n';
        if (data.logs) {
          output.textContent += data.logs.join('\\n');
        } else {
          output.textContent += 'No logs available\\n';
        }
        output.scrollTop = output.scrollHeight;
      })
      .catch(e => {
        document.getElementById('training-output').textContent += `\\n[!] Error loading logs: ${e.message}\\n`;
      });
    }
    
    function startAgentTraining() {
      const output = document.getElementById('training-output');
      output.textContent += '\\n[+] Starting agent training...\\n';
      
      fetch('/training/agent/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          output.textContent += `[+] Training started! Module: ${data.module || 'default'}\\n`;
          document.getElementById('agent-state').textContent = 'TRAINING';
          document.getElementById('agent-state').style.color = '#0ff';
        } else {
          output.textContent += `[!] Error: ${data.message}\\n`;
        }
        output.scrollTop = output.scrollHeight;
      })
      .catch(e => {
        output.textContent += `[!] Error: ${e.message}\\n`;
        output.scrollTop = output.scrollHeight;
      });
    }
    
    function viewTrainingProgress() {
      fetch('/training/progress')
      .then(r => r.json())
      .then(data => {
        const output = document.getElementById('training-output');
        output.textContent = '\\n=== TRAINING PROGRESS ===\\n';
        if (data.progress) {
          output.textContent += JSON.stringify(data.progress, null, 2);
        } else {
          output.textContent += 'No training data available\\n';
        }
        output.scrollTop = output.scrollHeight;
      })
      .catch(e => console.error('Training progress error:', e));
    }
    
    function deployAgent() {
      const output = document.getElementById('training-output');
      output.textContent += '\\n[+] Deploying agent...\\n';
      
      fetch('/ghost/deploy', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          output.textContent += `[+] Agent deployed! ID: ${data.agent_id || 'N/A'}\\n`;
          document.getElementById('agent-state').textContent = 'DEPLOYED';
          document.getElementById('agent-state').style.color = '#0f0';
        } else {
          output.textContent += `[!] Error: ${data.message}\\n`;
        }
        output.scrollTop = output.scrollHeight;
      })
      .catch(e => {
        output.textContent += `[!] Error: ${e.message}\\n`;
        output.scrollTop = output.scrollHeight;
      });
    }
    
    function enterChallengeRoom(roomNum) {
      const output = document.getElementById('training-output');
      output.textContent += `\\n[+] Entering Challenge Room ${roomNum}...\\n`;
      
      fetch('/honeypot/room/enter', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({room: roomNum})
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          output.textContent += `[+] Entered Room ${roomNum}\\n`;
          output.textContent += data.message || '';
          output.textContent += '\\n';
        } else {
          output.textContent += `[!] Error: ${data.message}\\n`;
        }
        output.scrollTop = output.scrollHeight;
      })
      .catch(e => {
        output.textContent += `[!] Error: ${e.message}\\n`;
        output.scrollTop = output.scrollHeight;
      });
    }
    
    // Initialize Ghost when page loads
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => Ghost.init());
    } else {
      Ghost.init();
    }
    
    // Load voices
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
  </script>
</body>
</html>
"""

def auto_discover_master():
    """Auto-discover master node on local network"""
    import socket
    import threading
    
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None
    
    def scan_port(ip, port, timeout=0.5):
        """Check if port is open"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            s.close()
            return result == 0
        except:
            return False
    
    local_ip = get_local_ip()
    if not local_ip:
        return None
    
    # Known IPs (user provided)
    known_ips = ["192.168.1.116", "192.168.1.235", "192.168.1.14"]
    
    # Check known IPs first (faster)
    for ip in known_ips:
        if scan_port(ip, 7890, timeout=1.0):
            print(f"[AUTO-DISCOVERY] ✅ Found master at {ip}:7890")
            return ip
    
    # Get subnet and scan
    subnet = '.'.join(local_ip.split('.')[:3]) + '.'
    print(f"[AUTO-DISCOVERY] Scanning subnet {subnet}* for GhostHUD master...")
    
    found_ips = []
    threads = []
    for i in range(1, 255):
        ip = subnet + str(i)
        if ip == local_ip:
            continue
        t = threading.Thread(target=lambda ip=ip: found_ips.append(ip) if scan_port(ip, 7890, timeout=0.3) else None, daemon=True)
        t.start()
        threads.append(t)
        if len(threads) >= 50:
            for t in threads:
                t.join(timeout=0.5)
            threads = []
    
    for t in threads:
        t.join(timeout=0.5)
    
    if found_ips:
        master_ip = found_ips[0]
        print(f"[AUTO-DISCOVERY] ✅ Found master at {master_ip}:7890")
        return master_ip
    
    print("[AUTO-DISCOVERY] ⚠️ No master found, using default")
    return None

if __name__ == "__main__":
    try:
        if HTML is None:
            print("[!] CRITICAL: HTML not loaded!")
            sys.exit(1)

        # Get master IP with priority: CMD ARG > ENV VAR > AUTO-DISCOVERY > DEFAULT
        master_ip = None
        
        # Command line argument has highest priority
        if len(sys.argv) > 1:
            master_ip = sys.argv[1]
            print(f"[+] Using command-line master IP: {master_ip}")
        # Environment variable
        elif 'GHOST_MASTER_IP' in os.environ:
            master_ip = os.environ.get('GHOST_MASTER_IP')
            print(f"[+] Using environment variable master IP: {master_ip}")
        # Auto-discovery
        else:
            print("[+] Auto-discovering master node...")
            master_ip = auto_discover_master()
            if master_ip:
                print(f"[+] Auto-discovered master: {master_ip}")
            else:
                master_ip = "192.168.1.116"  # Default Linux master IP
                print(f"[+] Using default master IP: {master_ip}")

        # Create peer engine (auto-detect platform)
        engine = GhostOpsAdapter.create_peer_adapter(platform=None, master_ip=master_ip, local_port=7891)
        
        # HTML provider function
        def get_html():
            return HTML
        
        # Start peer server
        print(f"[+] Starting Windows Peer server on port 7891...")
        print(f"[+] HTML loaded: {len(HTML)} characters")

        # Auto-launch browser on Windows
        import threading
        import webbrowser
        def open_browser():
            import time
            time.sleep(2)  # Wait for server to start
            print("[+] 🌐 Opening browser at http://localhost:7891")
            webbrowser.open('http://localhost:7891')

        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        GhostOpsAdapter.start_peer_server(engine, get_html)
    except KeyboardInterrupt:
        print("[+] Shutting down")
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
