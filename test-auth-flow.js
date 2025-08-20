#!/usr/bin/env node

const axios = require('axios');

const FRONTEND_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8000';

async function testAuthFlow() {
    console.log('🧪 LocalAgentWeaver認証フローテスト開始\n');

    try {
        // テスト用ユーザー
        const testUser = {
            username: 'authtest',
            email: 'authtest@example.com',
            password: 'authtest123'
        };

        console.log('1️⃣ ユーザー登録テスト (フロントエンド経由)...');
        try {
            const registerResponse = await axios.post(`${FRONTEND_URL}/api/auth/register`, testUser, {
                headers: { 'Content-Type': 'application/json' }
            });
            
            console.log('✅ 登録成功:', registerResponse.data);
            console.log(`   ID: ${registerResponse.data.id}`);
            console.log(`   ユーザー名: ${registerResponse.data.username}`);
            console.log(`   メール: ${registerResponse.data.email}`);
            console.log('');
        } catch (error) {
            if (error.response?.data?.detail === 'Email already registered') {
                console.log('⚠️  ユーザーは既に存在します (継続)\n');
            } else {
                throw error;
            }
        }

        console.log('2️⃣ ログインテスト (フロントエンド経由)...');
        const loginResponse = await axios.post(`${FRONTEND_URL}/api/auth/login`, {
            email: testUser.email,
            password: testUser.password
        }, {
            headers: { 'Content-Type': 'application/json' }
        });

        const token = loginResponse.data.access_token;
        console.log('✅ ログイン成功');
        console.log(`   トークンタイプ: ${loginResponse.data.token_type}`);
        console.log(`   トークン: ${token.substring(0, 50)}...`);
        console.log('');

        console.log('3️⃣ 認証が必要なAPIテスト (バックエンド直接)...');
        const projectsResponse = await axios.get(`${BACKEND_URL}/api/projects/`, {
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        console.log('✅ 認証API呼び出し成功');
        console.log(`   プロジェクト数: ${projectsResponse.data.total || projectsResponse.data.length || 0}`);
        console.log('');

        console.log('4️⃣ プロジェクト作成テスト...');
        const newProject = {
            name: 'テストプロジェクト',
            description: '認証フローテスト用のプロジェクト'
        };

        const createProjectResponse = await axios.post(`${BACKEND_URL}/api/projects/`, newProject, {
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        console.log('✅ プロジェクト作成成功');
        console.log(`   プロジェクトID: ${createProjectResponse.data.id}`);
        console.log(`   プロジェクト名: ${createProjectResponse.data.name}`);
        console.log('');

        console.log('🎉 すべてのテストが正常に完了しました！');
        console.log('');
        console.log('📋 テスト結果サマリー:');
        console.log('   ✅ ユーザー登録');
        console.log('   ✅ ユーザーログイン');
        console.log('   ✅ JWT認証');
        console.log('   ✅ プロジェクト作成');
        console.log('');
        console.log('🌐 フロントエンドURL: http://localhost:3000');
        console.log('🔌 バックエンドAPI: http://localhost:8000');

    } catch (error) {
        console.error('❌ テスト失敗:', error.response?.data || error.message);
        process.exit(1);
    }
}

testAuthFlow();