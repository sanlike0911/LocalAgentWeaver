#!/usr/bin/env node

const axios = require('axios');

const FRONTEND_URL = 'http://localhost:3000';

async function simulateBrowserFlow() {
    console.log('🌐 ブラウザシミュレーション認証フローテスト\n');

    try {
        // 新しいユーザーでテスト
        const newUser = {
            username: 'browsertest',
            email: 'browsertest@example.com',
            password: 'browsertest123'
        };

        // Step 1: ログインページアクセス
        console.log('1️⃣ ログインページアクセス...');
        const loginPageResponse = await axios.get(`${FRONTEND_URL}/auth/login`);
        console.log(`✅ ログインページ表示: ${loginPageResponse.status} ${loginPageResponse.statusText}`);
        console.log('');

        // Step 2: 新規登録ページアクセス
        console.log('2️⃣ 新規登録ページアクセス...');
        const registerPageResponse = await axios.get(`${FRONTEND_URL}/auth/register`);
        console.log(`✅ 新規登録ページ表示: ${registerPageResponse.status} ${registerPageResponse.statusText}`);
        console.log('');

        // Step 3: 新規ユーザー登録
        console.log('3️⃣ フロントエンド経由でユーザー登録...');
        try {
            const registerApiResponse = await axios.post(`${FRONTEND_URL}/api/auth/register`, newUser, {
                headers: { 'Content-Type': 'application/json' }
            });
            console.log(`✅ ユーザー登録成功: ${registerApiResponse.data.username} (${registerApiResponse.data.email})`);
        } catch (error) {
            if (error.response?.data?.detail === 'Email already registered') {
                console.log('⚠️  ユーザーは既に存在します');
            } else {
                throw error;
            }
        }
        console.log('');

        // Step 4: フロントエンド経由でログイン
        console.log('4️⃣ フロントエンド経由でログイン...');
        const loginApiResponse = await axios.post(`${FRONTEND_URL}/api/auth/login`, {
            email: newUser.email,
            password: newUser.password
        }, {
            headers: { 'Content-Type': 'application/json' }
        });
        
        console.log(`✅ ログイン成功: トークン取得`);
        const token = loginApiResponse.data.access_token;
        console.log(`   トークン: ${token.substring(0, 30)}...`);
        console.log('');

        // Step 5: ダッシュボードページアクセス（認証後）
        console.log('5️⃣ ダッシュボードページアクセス...');
        const dashboardResponse = await axios.get(`${FRONTEND_URL}/dashboard`, {
            headers: {
                'Cookie': `token=${token}` // シミュレーション用
            }
        });
        console.log(`✅ ダッシュボードページ表示: ${dashboardResponse.status} ${dashboardResponse.statusText}`);
        console.log('');

        // Step 6: チャットページアクセステスト
        console.log('6️⃣ チャットページアクセステスト...');
        const chatResponse = await axios.get(`${FRONTEND_URL}/chat/1`);
        console.log(`✅ チャットページ表示: ${chatResponse.status} ${chatResponse.statusText}`);
        console.log('');

        console.log('🎉 ブラウザシミュレーションテスト完了！');
        console.log('');
        console.log('📋 確認完了項目:');
        console.log('   ✅ ログインページ表示');
        console.log('   ✅ 新規登録ページ表示');
        console.log('   ✅ フロントエンド経由ユーザー登録');
        console.log('   ✅ フロントエンド経由ログイン');
        console.log('   ✅ ダッシュボードページ表示');
        console.log('   ✅ チャットページ表示');
        console.log('');
        console.log('🔗 アクセス可能なURL:');
        console.log(`   📝 ログイン: ${FRONTEND_URL}/auth/login`);
        console.log(`   📝 新規登録: ${FRONTEND_URL}/auth/register`);
        console.log(`   📊 ダッシュボード: ${FRONTEND_URL}/dashboard`);
        console.log(`   💬 チャット: ${FRONTEND_URL}/chat/[プロジェクトID]`);

    } catch (error) {
        console.error('❌ ブラウザシミュレーションテスト失敗:', error.response?.data || error.message);
        process.exit(1);
    }
}

simulateBrowserFlow();