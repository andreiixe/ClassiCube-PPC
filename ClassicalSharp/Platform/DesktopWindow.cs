﻿// Copyright 2014-2017 ClassicalSharp | Licensed under BSD-3
using System;
using System.Drawing;
using OpenTK;
using OpenTK.Graphics;

namespace ClassicalSharp {
	
	/// <summary> Implementation of a native window and native input handling mechanism on Windows, OSX, and Linux. </summary>
	public sealed class DesktopWindow : GameWindow {
		
		Game game;
		public DesktopWindow(Game game, string username, bool nullContext, int width, int height) :
			base(width, height, GraphicsMode.Default, Program.AppName + " (" + username + ")", nullContext, 0, DisplayDevice.Primary) {
			this.game = game;
		}
		
		protected override void OnLoad(EventArgs e) {
			game.OnLoad();
			base.OnLoad(e);
		}
		
		public override void Dispose() {
			game.Dispose();
			base.Dispose();
		}
		
		protected override void OnRenderFrame(FrameEventArgs e) {
			game.RenderFrame(e.Time);
			base.OnRenderFrame(e);
		}
		
		protected override void OnResize(object sender, EventArgs e) {
			game.OnResize();
			base.OnResize(sender, e);
		}
		
		public void LoadIcon() {
			string launcherFile = "Launcher2.exe";
			if (!Platform.FileExists(launcherFile)) {
				launcherFile = "Launcher.exe";
			}
			if (!Platform.FileExists(launcherFile)) return;
			
			try {
				Icon = Icon.ExtractAssociatedIcon(launcherFile);
			} catch (Exception ex) {
				ErrorHandler.LogError("DesktopWindow.LoadIcon()", ex);
			}
		}
	}
}
