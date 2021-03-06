// Copyright 2017 Canonical Ltd.
// Licensed under the AGPLv3, see LICENCE file for details.

package caasoperator_test

import (
	"github.com/juju/testing"
	"github.com/juju/utils"
	"gopkg.in/juju/charm.v6"
	"gopkg.in/juju/names.v2"

	"github.com/juju/juju/apiserver/facades/agent/caasoperator"
	"github.com/juju/juju/environs/config"
	"github.com/juju/juju/network"
	"github.com/juju/juju/state"
	statetesting "github.com/juju/juju/state/testing"
	"github.com/juju/juju/status"
)

type mockState struct {
	testing.Stub
	app   mockApplication
	model mockModel
}

func newMockState() *mockState {
	ch := make(chan struct{}, 1)
	ch <- struct{}{}
	settingsWatcher := statetesting.NewMockNotifyWatcher(ch)
	return &mockState{
		app: mockApplication{
			charm: mockCharm{
				url:    charm.MustParseURL("cs:gitlab-1"),
				sha256: "fake-sha256",
			},
			settings:        charm.Settings{"k": 123},
			settingsWatcher: settingsWatcher,
		},
	}
}

func (st *mockState) Application(id string) (caasoperator.Application, error) {
	st.MethodCall(st, "Application", id)
	if err := st.NextErr(); err != nil {
		return nil, err
	}
	return &st.app, nil
}

func (st *mockState) Model() (caasoperator.Model, error) {
	st.MethodCall(st, "Model")
	if err := st.NextErr(); err != nil {
		return nil, err
	}
	return &st.model, nil
}

func (st *mockState) APIHostPortsForAgents() ([][]network.HostPort, error) {
	st.MethodCall(st, "APIHostPortsForAgents")
	if err := st.NextErr(); err != nil {
		return nil, err
	}
	hps := [][]network.HostPort{
		network.NewHostPorts(1234, "0.1.2.3"),
		network.NewHostPorts(1234, "0.1.2.4"),
		network.NewHostPorts(1234, "0.1.2.5"),
	}
	return hps, nil
}

type mockModel struct {
	testing.Stub
}

func (m *mockModel) SetContainerSpec(tag names.Tag, spec string) error {
	m.MethodCall(m, "SetContainerSpec", tag, spec)
	return m.NextErr()
}

func (st *mockModel) Name() string {
	return "some-model"
}

func (m *mockModel) Config() (*config.Config, error) {
	m.MethodCall(m, "Config")
	if err := m.NextErr(); err != nil {
		return nil, err
	}
	return config.New(config.UseDefaults, map[string]interface{}{
		"name":       "some-model",
		"type":       "kubernetes",
		"uuid":       utils.MustNewUUID().String(),
		"http-proxy": "http.proxy",
	})
}

type mockApplication struct {
	testing.Stub
	charm           mockCharm
	forceUpgrade    bool
	settings        charm.Settings
	settingsWatcher *statetesting.MockNotifyWatcher
}

func (app *mockApplication) SetStatus(info status.StatusInfo) error {
	app.MethodCall(app, "SetStatus", info)
	return app.NextErr()
}

func (app *mockApplication) Charm() (caasoperator.Charm, bool, error) {
	app.MethodCall(app, "Charm")
	if err := app.NextErr(); err != nil {
		return nil, false, err
	}
	return &app.charm, app.forceUpgrade, nil
}

func (app *mockApplication) CharmConfig() (charm.Settings, error) {
	app.MethodCall(app, "CharmConfig")
	if err := app.NextErr(); err != nil {
		return nil, err
	}
	return app.settings, nil
}

func (app *mockApplication) WatchCharmConfig() (state.NotifyWatcher, error) {
	app.MethodCall(app, "WatchCharmConfig")
	if err := app.NextErr(); err != nil {
		return nil, err
	}
	return app.settingsWatcher, nil
}

type mockCharm struct {
	url    *charm.URL
	sha256 string
}

func (ch *mockCharm) URL() *charm.URL {
	return ch.url
}

func (ch *mockCharm) BundleSha256() string {
	return ch.sha256
}
